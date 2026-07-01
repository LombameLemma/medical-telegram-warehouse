"""
Configuration management for the medical telegram warehouse project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Telegram API Configuration
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'medical_warehouse')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)

# Data Paths
DATA_RAW_PATH = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED_PATH = PROJECT_ROOT / 'data' / 'processed'
TELEGRAM_MESSAGES_PATH = DATA_RAW_PATH / 'telegram_messages'
IMAGES_PATH = DATA_RAW_PATH / 'images'
LOGS_PATH = PROJECT_ROOT / 'logs'

# Create directories if they don't exist
for path in [DATA_RAW_PATH, DATA_PROCESSED_PATH, TELEGRAM_MESSAGES_PATH, IMAGES_PATH, LOGS_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Telegram Channels to Scrape
TELEGRAM_CHANNELS = [
    'CheMed123',  # Replace with actual channel username
    'lobeliacosmetics',  # Replace with actual channel username
    'tikvahpharma',  # Replace with actual channel username
    # Add more channels from et.tgstat.com/medicine
]

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# API Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))

# YOLO Configuration
YOLO_MODEL = 'yolov8n.pt'  # Nano model for efficiency
YOLO_CONFIDENCE_THRESHOLD = 0.25

# Validate critical configuration
def validate_config():
    """Validate that critical configuration is present."""
    if not TELEGRAM_API_ID:
        raise ValueError("TELEGRAM_API_ID is not set in environment variables")
    if not TELEGRAM_API_HASH:
        raise ValueError("TELEGRAM_API_HASH is not set in environment variables")
    if not TELEGRAM_PHONE:
        raise ValueError("TELEGRAM_PHONE is not set in environment variables")
    return True
