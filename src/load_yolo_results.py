"""
Load YOLO Detection Results to PostgreSQL
Loads YOLO detection CSV into the raw schema.
"""
import csv
from pathlib import Path
from loguru import logger

import psycopg2
from psycopg2.extras import execute_values

from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DATA_PROCESSED_PATH,
    LOGS_PATH
)

# Configure logging
logger.add(
    LOGS_PATH / "load_yolo_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)


class YOLOResultsLoader:
    """Loader for YOLO detection results."""
    
    def __init__(self):
        """Initialize database connection."""
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        self.conn.autocommit = False
        logger.info("Connected to PostgreSQL database")
    
    def create_yolo_table(self):
        """Create raw.yolo_detections table if it doesn't exist."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS raw.yolo_detections (
                    message_id BIGINT PRIMARY KEY,
                    channel_name VARCHAR(255),
                    image_path TEXT,
                    image_category VARCHAR(50),
                    detected_classes TEXT,
                    num_detections INTEGER,
                    avg_confidence DECIMAL(5, 4),
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_yolo_channel 
                ON raw.yolo_detections(channel_name);
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_yolo_category 
                ON raw.yolo_detections(image_category);
            """)
            
            self.conn.commit()
            logger.info("Created raw.yolo_detections table")
    
    def load_csv(self, csv_path: Path):
        """
        Load YOLO results from CSV file.
        
        Args:
            csv_path: Path to the CSV file
        """
        logger.info(f"Loading YOLO results from {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            logger.warning("No data to load")
            return
        
        # Prepare values for insertion
        values = [
            (
                int(row['message_id']),
                row['channel_name'],
                row['image_path'],
                row['image_category'],
                row['detected_classes'],
                int(row['num_detections']),
                float(row['avg_confidence'])
            )
            for row in rows
        ]
        
        # Insert with ON CONFLICT
        insert_query = """
            INSERT INTO raw.yolo_detections (
                message_id, channel_name, image_path, image_category,
                detected_classes, num_detections, avg_confidence
            ) VALUES %s
            ON CONFLICT (message_id) 
            DO UPDATE SET
                image_category = EXCLUDED.image_category,
                detected_classes = EXCLUDED.detected_classes,
                num_detections = EXCLUDED.num_detections,
                avg_confidence = EXCLUDED.avg_confidence,
                loaded_at = CURRENT_TIMESTAMP;
        """
        
        try:
            with self.conn.cursor() as cur:
                execute_values(cur, insert_query, values)
            self.conn.commit()
            logger.info(f"Loaded {len(values)} YOLO detection results")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error loading YOLO results: {e}")
    
    def get_statistics(self):
        """Print statistics about loaded YOLO results."""
        with self.conn.cursor() as cur:
            # Total detections
            cur.execute("SELECT COUNT(*) FROM raw.yolo_detections;")
            total = cur.fetchone()[0]
            
            # By category
            cur.execute("""
                SELECT image_category, COUNT(*) as count
                FROM raw.yolo_detections
                GROUP BY image_category
                ORDER BY count DESC;
            """)
            by_category = cur.fetchall()
            
            # Average detections
            cur.execute("""
                SELECT AVG(num_detections), AVG(avg_confidence)
                FROM raw.yolo_detections;
            """)
            avg_stats = cur.fetchone()
        
        logger.info("=" * 50)
        logger.info("YOLO RESULTS STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total images: {total}")
        logger.info(f"Avg detections per image: {avg_stats[0]:.2f}")
        logger.info(f"Avg confidence: {avg_stats[1]:.4f}")
        logger.info("\nImages by category:")
        for cat, count in by_category:
            logger.info(f"  {cat}: {count}")
        logger.info("=" * 50)
    
    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("Closed database connection")


def main():
    """Main function to load YOLO results."""
    csv_file = DATA_PROCESSED_PATH / 'yolo_detections.csv'
    
    if not csv_file.exists():
        logger.error(f"YOLO results file not found: {csv_file}")
        logger.info("Please run yolo_detect.py first to generate detection results")
        return
    
    loader = YOLOResultsLoader()
    
    try:
        # Create table
        loader.create_yolo_table()
        
        # Load CSV
        loader.load_csv(csv_file)
        
        # Print statistics
        loader.get_statistics()
    
    finally:
        loader.close()


if __name__ == '__main__':
    logger.info("Starting YOLO results loader")
    main()
    logger.info("YOLO results loading completed")
