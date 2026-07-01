"""
Load Raw Data to PostgreSQL
Loads JSON files from the data lake into a raw PostgreSQL schema.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from loguru import logger

import psycopg2
from psycopg2.extras import execute_values

from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    TELEGRAM_MESSAGES_PATH,
    LOGS_PATH
)

# Configure logging
logger.add(
    LOGS_PATH / "load_raw_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)


class RawDataLoader:
    """Loader for raw Telegram data into PostgreSQL."""
    
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
    
    def create_raw_schema(self):
        """Create raw schema and tables if they don't exist."""
        with self.conn.cursor() as cur:
            # Create raw schema
            cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
            
            # Create raw.telegram_messages table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                    message_id BIGINT,
                    channel_name VARCHAR(255),
                    channel_username VARCHAR(255),
                    message_date TIMESTAMP,
                    message_text TEXT,
                    has_media BOOLEAN,
                    image_path TEXT,
                    views INTEGER,
                    forwards INTEGER,
                    scraped_at TIMESTAMP,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (channel_username, message_id)
                );
            """)
            
            # Create index on message_date for faster queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_date 
                ON raw.telegram_messages(message_date);
            """)
            
            # Create index on channel_username
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_channel_username 
                ON raw.telegram_messages(channel_username);
            """)
            
            self.conn.commit()
            logger.info("Created raw schema and tables")
    
    def load_json_file(self, file_path: Path) -> List[Dict]:
        """
        Load messages from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of message dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            logger.info(f"Loaded {len(messages)} messages from {file_path}")
            return messages
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []
    
    def insert_messages(self, messages: List[Dict]):
        """
        Insert messages into the raw.telegram_messages table.
        
        Args:
            messages: List of message dictionaries
        """
        if not messages:
            return
        
        # Prepare data for insertion
        values = [
            (
                msg['message_id'],
                msg['channel_name'],
                msg['channel_username'],
                msg['message_date'],
                msg['message_text'],
                msg['has_media'],
                msg['image_path'],
                msg['views'],
                msg['forwards'],
                msg['scraped_at']
            )
            for msg in messages
        ]
        
        # Insert with ON CONFLICT to handle duplicates
        insert_query = """
            INSERT INTO raw.telegram_messages (
                message_id, channel_name, channel_username, message_date,
                message_text, has_media, image_path, views, forwards, scraped_at
            ) VALUES %s
            ON CONFLICT (channel_username, message_id) 
            DO UPDATE SET
                views = EXCLUDED.views,
                forwards = EXCLUDED.forwards,
                loaded_at = CURRENT_TIMESTAMP;
        """
        
        try:
            with self.conn.cursor() as cur:
                execute_values(cur, insert_query, values)
            self.conn.commit()
            logger.info(f"Inserted/updated {len(messages)} messages")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting messages: {e}")
    
    def load_all_messages(self):
        """Load all JSON files from the data lake into PostgreSQL."""
        json_files = list(TELEGRAM_MESSAGES_PATH.rglob('*.json'))
        logger.info(f"Found {len(json_files)} JSON files to load")
        
        total_messages = 0
        for json_file in json_files:
            messages = self.load_json_file(json_file)
            self.insert_messages(messages)
            total_messages += len(messages)
        
        logger.info(f"Loaded {total_messages} total messages into PostgreSQL")
    
    def get_statistics(self):
        """Print statistics about the loaded data."""
        with self.conn.cursor() as cur:
            # Total messages
            cur.execute("SELECT COUNT(*) FROM raw.telegram_messages;")
            total = cur.fetchone()[0]
            
            # Messages by channel
            cur.execute("""
                SELECT channel_name, COUNT(*) as count
                FROM raw.telegram_messages
                GROUP BY channel_name
                ORDER BY count DESC;
            """)
            by_channel = cur.fetchall()
            
            # Messages with media
            cur.execute("""
                SELECT COUNT(*) 
                FROM raw.telegram_messages 
                WHERE has_media = true;
            """)
            with_media = cur.fetchone()[0]
            
            # Date range
            cur.execute("""
                SELECT MIN(message_date), MAX(message_date)
                FROM raw.telegram_messages;
            """)
            date_range = cur.fetchone()
        
        logger.info("=" * 50)
        logger.info("DATA STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total messages: {total}")
        logger.info(f"Messages with media: {with_media}")
        logger.info(f"Date range: {date_range[0]} to {date_range[1]}")
        logger.info("\nMessages by channel:")
        for channel, count in by_channel:
            logger.info(f"  {channel}: {count}")
        logger.info("=" * 50)
    
    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("Closed database connection")


def main():
    """Main function to load raw data."""
    loader = RawDataLoader()
    
    try:
        # Create schema and tables
        loader.create_raw_schema()
        
        # Load all messages
        loader.load_all_messages()
        
        # Print statistics
        loader.get_statistics()
    
    finally:
        loader.close()


if __name__ == '__main__':
    logger.info("Starting raw data loader")
    main()
    logger.info("Raw data loading completed")
