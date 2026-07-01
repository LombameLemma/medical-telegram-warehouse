# Medical Telegram Data Warehouse

An end-to-end data pipeline for extracting, transforming, and analyzing medical business data from Ethiopian Telegram channels.

## Project Overview

This project implements a modern ELT (Extract, Load, Transform) pipeline that:
- Scrapes data from public Telegram channels selling medical/pharmaceutical products
- Stores raw data in a structured data lake
- Transforms data using dbt into a dimensional star schema
- Enriches data using YOLOv8 object detection on images
- Exposes insights through a FastAPI analytical API
- Orchestrates the entire pipeline using Dagster

## Business Questions Answered

1. What are the top 10 most frequently mentioned medical products?
2. How does product pricing/availability vary across channels?
3. Which channels have the most visual content?
4. What are the daily/weekly trends in posting volume?

## Architecture

```
Telegram Channels → Raw Data Lake → PostgreSQL → dbt Transformation → Data Marts → FastAPI
                         ↓
                    YOLO Detection → Image Enrichment
                         ↓
                    Dagster Orchestration
```

## Tech Stack

- **Data Extraction**: Telethon (Telegram API)
- **Data Storage**: PostgreSQL (Data Warehouse)
- **Transformation**: dbt (Data Build Tool)
- **Enrichment**: YOLOv8 (Ultralytics)
- **API**: FastAPI
- **Orchestration**: Dagster
- **Containerization**: Docker

## Project Structure

```
medical-telegram-warehouse/
├── .env                          # Secrets (DO NOT COMMIT)
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── data/
│   ├── raw/
│   │   ├── telegram_messages/    # JSON files by date/channel
│   │   └── images/               # Downloaded images
│   └── processed/
├── medical_warehouse/            # dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   └── tests/
├── src/
│   ├── scraper.py               # Telegram scraper
│   ├── yolo_detect.py           # Object detection
│   └── load_raw_data.py         # Load JSON to PostgreSQL
├── api/
│   ├── main.py                  # FastAPI application
│   ├── database.py              # DB connection
│   └── schemas.py               # Pydantic models
├── notebooks/                   # Exploratory analysis
├── tests/                       # Unit tests
├── scripts/                     # Utility scripts
├── logs/                        # Application logs
└── pipeline.py                  # Dagster pipeline definition
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Docker & Docker Compose (optional)
- Telegram API credentials (from my.telegram.org)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd medical-telegram-warehouse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file:

```env
# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone_number

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medical_warehouse
DB_USER=postgres
DB_PASSWORD=your_password
```

### 4. Database Setup

```bash
# Start PostgreSQL (if using Docker)
docker-compose up -d postgres

# Create database
psql -U postgres -c "CREATE DATABASE medical_warehouse;"
```

### 5. Run the Pipeline

```bash
# Step 1: Scrape Telegram data
python src/scraper.py

# Step 2: Load raw data to PostgreSQL
python src/load_raw_data.py

# Step 3: Run dbt transformations
cd medical_warehouse
dbt run
dbt test

# Step 4: Run YOLO detection
python src/yolo_detect.py

# Step 5: Start the API
uvicorn api.main:app --reload

# Step 6: Run orchestrated pipeline
dagster dev -f pipeline.py
```

## Data Sources

- **CheMed**: Medical products
- **Lobelia Cosmetics**: Cosmetics and health products
- **Tikvah Pharma**: Pharmaceuticals
- Additional channels from et.tgstat.com/medicine

## Data Model

### Star Schema

**Fact Table:**
- `fct_messages`: Core message data with metrics
- `fct_image_detections`: YOLO detection results

**Dimension Tables:**
- `dim_channels`: Channel information
- `dim_dates`: Date dimension for time-series analysis

## API Endpoints

- `GET /api/reports/top-products?limit=10` - Top mentioned products
- `GET /api/channels/{channel_name}/activity` - Channel activity stats
- `GET /api/search/messages?query=keyword` - Search messages
- `GET /api/reports/visual-content` - Visual content statistics

## Testing

```bash
# Run unit tests
pytest tests/

# Run dbt tests
cd medical_warehouse
dbt test
```

## Documentation

- **dbt docs**: `dbt docs generate && dbt docs serve`
- **API docs**: Navigate to `http://localhost:8000/docs`
- **Dagster UI**: `http://localhost:3000`

## Team

- **Tutors**: Kerod, Mahbubah, Feven
- **Support**: Slack #all-week8
- **Office Hours**: Mon-Fri, 08:00-15:00 UTC

## Key Dates

- **Challenge Introduction**: June 24, 2026
- **Interim Submission**: June 28, 2026, 8:00 PM UTC
- **Final Submission**: June 30, 2026, 8:00 PM UTC

## License

MIT License

## Contributing

This is an educational project. Please follow the submission guidelines provided.
