"""
YOLO Object Detection for Telegram Images
Uses YOLOv8 to detect objects in scraped images and classify them.
"""
import csv
from pathlib import Path
from typing import List, Dict, Tuple
from loguru import logger

from ultralytics import YOLO
import cv2

from config import IMAGES_PATH, DATA_PROCESSED_PATH, LOGS_PATH, YOLO_MODEL, YOLO_CONFIDENCE_THRESHOLD

# Configure logging
logger.add(
    LOGS_PATH / "yolo_detect_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)


class ImageDetector:
    """YOLO-based object detector for medical telegram images."""
    
    # Object classes that indicate different image types
    PERSON_CLASSES = ['person']
    PRODUCT_CLASSES = ['bottle', 'cup', 'bowl', 'vase', 'handbag', 'backpack', 'suitcase']
    
    def __init__(self, model_name: str = YOLO_MODEL):
        """
        Initialize the YOLO detector.
        
        Args:
            model_name: Name of the YOLO model to use
        """
        logger.info(f"Loading YOLO model: {model_name}")
        self.model = YOLO(model_name)
        self.confidence_threshold = YOLO_CONFIDENCE_THRESHOLD
        logger.info("YOLO model loaded successfully")
    
    def detect_objects(self, image_path: Path) -> List[Dict]:
        """
        Run object detection on an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of detected objects with class names and confidence scores
        """
        try:
            # Run inference
            results = self.model(str(image_path), conf=self.confidence_threshold, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get class name and confidence
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    detections.append({
                        'class': class_name,
                        'confidence': confidence
                    })
            
            return detections
        
        except Exception as e:
            logger.error(f"Error detecting objects in {image_path}: {e}")
            return []
    
    def classify_image(self, detections: List[Dict]) -> Tuple[str, str]:
        """
        Classify image based on detected objects.
        
        Args:
            detections: List of detected objects
            
        Returns:
            Tuple of (category, detected_classes_string)
        """
        if not detections:
            return 'other', ''
        
        # Extract unique detected classes
        detected_classes = set(d['class'] for d in detections)
        detected_classes_str = ','.join(sorted(detected_classes))
        
        # Check for person and product
        has_person = any(cls in self.PERSON_CLASSES for cls in detected_classes)
        has_product = any(cls in self.PRODUCT_CLASSES for cls in detected_classes)
        
        # Classify based on presence of person and product
        if has_person and has_product:
            category = 'promotional'
        elif has_product and not has_person:
            category = 'product_display'
        elif has_person and not has_product:
            category = 'lifestyle'
        else:
            category = 'other'
        
        return category, detected_classes_str
    
    def process_image(self, image_path: Path, channel_name: str) -> Dict:
        """
        Process a single image: detect objects and classify.
        
        Args:
            image_path: Path to the image
            channel_name: Name of the channel
            
        Returns:
            Dictionary with detection results
        """
        logger.info(f"Processing: {image_path}")
        
        # Extract message_id from filename
        message_id = image_path.stem
        
        # Detect objects
        detections = self.detect_objects(image_path)
        
        # Classify image
        category, detected_classes = self.classify_image(detections)
        
        # Calculate average confidence
        if detections:
            avg_confidence = sum(d['confidence'] for d in detections) / len(detections)
        else:
            avg_confidence = 0.0
        
        result = {
            'message_id': message_id,
            'channel_name': channel_name,
            'image_path': str(image_path.relative_to(IMAGES_PATH.parent)),
            'image_category': category,
            'detected_classes': detected_classes,
            'num_detections': len(detections),
            'avg_confidence': round(avg_confidence, 4),
            'detections': detections
        }
        
        logger.info(f"  Category: {category}, Detections: {len(detections)}")
        return result
    
    def process_all_images(self) -> List[Dict]:
        """
        Process all images in the data directory.
        
        Returns:
            List of detection results for all images
        """
        logger.info("Starting to process all images")
        
        # Find all image files
        image_files = list(IMAGES_PATH.rglob('*.jpg')) + list(IMAGES_PATH.rglob('*.jpeg')) + list(IMAGES_PATH.rglob('*.png'))
        logger.info(f"Found {len(image_files)} images to process")
        
        results = []
        for i, image_path in enumerate(image_files, 1):
            # Get channel name from directory structure
            channel_name = image_path.parent.name
            
            # Process image
            result = self.process_image(image_path, channel_name)
            results.append(result)
            
            # Log progress
            if i % 10 == 0:
                logger.info(f"Processed {i}/{len(image_files)} images")
        
        logger.info(f"Completed processing {len(results)} images")
        return results
    
    def save_results(self, results: List[Dict], output_file: Path):
        """
        Save detection results to a CSV file.
        
        Args:
            results: List of detection results
            output_file: Path to output CSV file
        """
        if not results:
            logger.warning("No results to save")
            return
        
        # Prepare CSV data (excluding the detailed detections list)
        csv_data = [
            {
                'message_id': r['message_id'],
                'channel_name': r['channel_name'],
                'image_path': r['image_path'],
                'image_category': r['image_category'],
                'detected_classes': r['detected_classes'],
                'num_detections': r['num_detections'],
                'avg_confidence': r['avg_confidence']
            }
            for r in results
        ]
        
        # Write to CSV
        fieldnames = ['message_id', 'channel_name', 'image_path', 'image_category', 
                     'detected_classes', 'num_detections', 'avg_confidence']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        logger.info(f"Saved results to {output_file}")
    
    def print_statistics(self, results: List[Dict]):
        """Print statistics about the detection results."""
        if not results:
            logger.warning("No results to analyze")
            return
        
        # Count by category
        categories = {}
        for r in results:
            cat = r['image_category']
            categories[cat] = categories.get(cat, 0) + 1
        
        # Count by channel
        channels = {}
        for r in results:
            ch = r['channel_name']
            channels[ch] = channels.get(ch, 0) + 1
        
        # Average detections
        avg_detections = sum(r['num_detections'] for r in results) / len(results)
        
        logger.info("=" * 50)
        logger.info("DETECTION STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total images processed: {len(results)}")
        logger.info(f"Average detections per image: {avg_detections:.2f}")
        logger.info("\nImages by category:")
        for cat, count in sorted(categories.items()):
            logger.info(f"  {cat}: {count} ({count/len(results)*100:.1f}%)")
        logger.info("\nImages by channel:")
        for ch, count in sorted(channels.items()):
            logger.info(f"  {ch}: {count}")
        logger.info("=" * 50)


def main():
    """Main function to run YOLO detection."""
    # Initialize detector
    detector = ImageDetector()
    
    # Process all images
    results = detector.process_all_images()
    
    # Save results
    output_file = DATA_PROCESSED_PATH / 'yolo_detections.csv'
    detector.save_results(results, output_file)
    
    # Print statistics
    detector.print_statistics(results)


if __name__ == '__main__':
    logger.info("Starting YOLO object detection")
    main()
    logger.info("YOLO detection completed")
