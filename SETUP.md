# Setup Guide

This guide will help you set up and run the Medical Telegram Data Warehouse project.

## Prerequisites

### Required Software
- **Python 3.9+**: Download from [python.org](https://www.python.org/downloads/)
- **PostgreSQL 13+**: Download from [postgresql.org](https://www.postgresql.org/download/)
- **Git**: For version control

### Optional Software
- **Docker & Docker Compose**: For containerized deployment
- **VS Code**: Recommended IDE

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd medical-telegram-warehouse
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Get Telegram API Credentials

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Navigate to "API development tools"
4. Create a new application
5. Note down your `api_id` and `api_hash`

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `.env` and fill in your credentials:

```env
# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+251900000000

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medical_warehouse
DB_USER=postgres
DB_PASSWORD=your_password
```

### 6. Setup PostgreSQL Database

#### Option A: Using Local PostgreSQL

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE medical_warehouse;

# Exit
\q
```

#### Option B: Using Docker

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Wait for it to be ready (about 10 seconds)
```

### 7. Initialize Database Schema

```bash
# Run the initialization script
psql -U postgres -d medical_warehouse -f scripts/init_db.sql
```

### 8. Update Channel Usernames

Edit `src/config.py` and update the `TELEGRAM_CHANNELS` list with actual channel usernames:

```python
TELEGRAM_CHANNELS = [
    'actual_channel_username_1',
    'actual_channel_username_2',
    # Add more channels
]
```

To find channel usernames:
1. Open Telegram
2. Go to the channel
3. Look at the channel info or URL (t.me/username)

### 9. Install dbt Packages

```bash
cd medical_warehouse
dbt deps
cd ..
```

### 10. Download YOLO Model

The YOLO model will download automatically on first run. To pre-download:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

## Running the Pipeline

### Manual Execution (Recommended for First Run)

Run each step manually to verify everything works:

```bash
# Step 1: Scrape Telegram data
python src/scraper.py

# Step 2: Load raw data to PostgreSQL
python src/load_raw_data.py

# Step 3: Run dbt transformations
cd medical_warehouse
dbt run
dbt test
cd ..

# Step 4: Run YOLO detection
python src/yolo_detect.py

# Step 5: Load YOLO results
python src/load_yolo_results.py

# Step 6: Rebuild marts with YOLO data
cd medical_warehouse
dbt run --select fct_image_detections
cd ..
```

### Using Dagster Orchestration

```bash
# Start Dagster UI
dagster dev -f pipeline.py

# Open browser to http://localhost:3000
# Click "Launchpad" and run the pipeline
```

### Start the API

```bash
# In a new terminal
uvicorn api.main:app --reload

# API will be available at:
# - Swagger docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

## Verification

### Verify Data Lake

```bash
# Check if JSON files were created
dir data\raw\telegram_messages  # Windows
ls data/raw/telegram_messages   # Linux/Mac
```

### Verify Database

```bash
# Connect to database
psql -U postgres -d medical_warehouse

# Check raw data
SELECT COUNT(*) FROM raw.telegram_messages;

# Check dimensional tables
SELECT COUNT(*) FROM marts.fct_messages;
SELECT COUNT(*) FROM marts.dim_channels;
SELECT COUNT(*) FROM marts.dim_dates;

# Exit
\q
```

### Verify YOLO Results

```bash
# Check CSV file
dir data\processed  # Windows
ls data/processed   # Linux/Mac

# Should see yolo_detections.csv
```

### Test API Endpoints

```bash
# Test health
curl http://localhost:8000/health

# Test channels
curl http://localhost:8000/api/channels

# Or open http://localhost:8000/docs in browser
```

## Troubleshooting

### Issue: Telegram Authentication Failed

**Solution**: 
- Verify API credentials in `.env`
- Delete `medical_scraper_session.session` file and try again
- Check phone number format (+country code)

### Issue: Database Connection Error

**Solution**:
- Verify PostgreSQL is running: `pg_isadmin`
- Check credentials in `.env`
- Verify database exists: `psql -U postgres -l`

### Issue: dbt Command Not Found

**Solution**:
```bash
pip install dbt-core dbt-postgres
```

### Issue: YOLO Model Download Fails

**Solution**:
- Check internet connection
- Manually download from [Ultralytics](https://github.com/ultralytics/assets/releases)
- Place `yolov8n.pt` in project root

### Issue: No Images Found

**Solution**:
- Verify channels have recent posts with images
- Check `data/raw/images` directory permissions
- Some channels may not allow media download

### Issue: Import Errors

**Solution**:
```bash
# Ensure virtual environment is activated
# Re-install dependencies
pip install -r requirements.txt --force-reinstall
```

## Development Tips

### View Logs

```bash
# View scraper logs
type logs\scraper_*.log  # Windows
cat logs/scraper_*.log   # Linux/Mac

# View dbt logs
type medical_warehouse\logs\dbt.log  # Windows
cat medical_warehouse/logs/dbt.log   # Linux/Mac
```

### Run Tests

```bash
pytest tests/ -v
```

### Generate dbt Documentation

```bash
cd medical_warehouse
dbt docs generate
dbt docs serve
# Opens browser to http://localhost:8080
```

### Reset Everything

```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE IF EXISTS medical_warehouse;"
psql -U postgres -c "CREATE DATABASE medical_warehouse;"
psql -U postgres -d medical_warehouse -f scripts/init_db.sql

# Clear data lake
rmdir /s data\raw  # Windows
rm -rf data/raw    # Linux/Mac

# Re-run pipeline
```

## Next Steps

1. **Customize Channels**: Add more Ethiopian medical channels
2. **Enhance NLP**: Improve product extraction in API
3. **Add Visualizations**: Create dashboards with the data
4. **Schedule Pipeline**: Set up automated daily runs
5. **Deploy**: Deploy API to production server

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review dbt documentation
- Ask in Slack channel: #all-week8
- Office hours: Mon-Fri, 08:00-15:00 UTC

## Resources

- [Telethon Documentation](https://docs.telethon.dev/)
- [dbt Documentation](https://docs.getdbt.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Dagster Documentation](https://docs.dagster.io/)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
