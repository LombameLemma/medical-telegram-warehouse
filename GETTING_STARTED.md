# Getting Started Guide

Welcome to the Medical Telegram Data Warehouse project! This guide will help you get up and running quickly.

## Quick Start (5 Minutes)

### 1. Install Python Dependencies

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Environment Variables

```cmd
copy .env.example .env
```

Edit `.env` file and add your credentials:
- Get Telegram API credentials from https://my.telegram.org
- Set PostgreSQL password

### 3. Start PostgreSQL Database

Using Docker (easiest):
```cmd
docker-compose up -d postgres
```

Or use your local PostgreSQL installation.

### 4. Run Setup Check

```cmd
python quickstart.py
```

This will verify your setup and show any issues.

### 5. Update Channel List

Edit `src\config.py` and update the `TELEGRAM_CHANNELS` list with actual channel usernames.

## First Pipeline Run (30 Minutes)

### Step 1: Scrape Data

```cmd
python src\scraper.py
```

What happens:
- Connects to Telegram API
- Downloads messages from configured channels
- Saves to `data/raw/telegram_messages/`
- Downloads images to `data/raw/images/`

Expected output: JSON files organized by date and channel

### Step 2: Load to Database

```cmd
python src\load_raw_data.py
```

What happens:
- Reads JSON files from data lake
- Creates raw schema and tables
- Loads data into PostgreSQL
- Shows statistics

Expected output: Data in `raw.telegram_messages` table

### Step 3: Run dbt Transformations

```cmd
cd medical_warehouse
dbt deps
dbt run
dbt test
cd ..
```

What happens:
- Installs dbt packages
- Creates staging views
- Builds dimensional tables
- Runs all tests

Expected output: Tables in `marts` schema

### Step 4: Run YOLO Detection

```cmd
python src\yolo_detect.py
```

What happens:
- Downloads YOLOv8 model (first run only)
- Processes all images
- Detects objects and classifies images
- Saves results to CSV

Expected output: `data/processed/yolo_detections.csv`

### Step 5: Load YOLO Results

```cmd
python src\load_yolo_results.py
```

What happens:
- Loads CSV to PostgreSQL
- Creates `raw.yolo_detections` table
- Shows statistics

### Step 6: Rebuild Image Detections

```cmd
cd medical_warehouse
dbt run --select fct_image_detections
cd ..
```

What happens:
- Joins YOLO results with messages
- Creates enriched image fact table

### Step 7: Start the API

```cmd
uvicorn api.main:app --reload
```

What happens:
- Starts FastAPI server on port 8000
- Connects to PostgreSQL
- Serves analytical endpoints

Test it: Open http://localhost:8000/docs in your browser

## Using Dagster (Automated Pipeline)

Instead of running steps manually, use Dagster:

```cmd
dagster dev -f pipeline.py
```

What happens:
- Opens Dagster UI at http://localhost:3000
- Shows pipeline graph
- Allows you to run the entire pipeline
- Provides monitoring and logging

To run:
1. Click "Launchpad"
2. Click "Launch Run"
3. Watch the execution in real-time

## Verify Everything Works

### Check Data Lake

```cmd
dir data\raw\telegram_messages
dir data\raw\images
```

Should see JSON files and image directories.

### Check Database

```cmd
psql -U postgres -d medical_warehouse

-- Check raw data
SELECT COUNT(*) FROM raw.telegram_messages;

-- Check marts
SELECT * FROM marts.dim_channels;
SELECT COUNT(*) FROM marts.fct_messages;

-- Exit
\q
```

### Check API

Open http://localhost:8000/docs and try:
- GET /health
- GET /api/channels
- GET /api/reports/top-products?limit=5

### Check dbt Documentation

```cmd
cd medical_warehouse
dbt docs generate
dbt docs serve
```

Opens http://localhost:8080 with interactive documentation.

## Common First-Time Issues

### Issue 1: Telegram Authentication

**Symptom**: "Please enter your phone number"

**Solution**: 
- The first time you run the scraper, Telethon needs to authenticate
- You'll receive a code via Telegram
- Enter the code when prompted
- A session file will be created for future runs

### Issue 2: No Data Scraped

**Symptom**: Empty JSON files or no files created

**Solution**:
- Verify channel usernames are correct (check Telegram app)
- Some channels may be private or restricted
- Try with public channels first
- Check logs in `logs/scraper_*.log`

### Issue 3: Database Connection Failed

**Symptom**: "could not connect to server"

**Solution**:
- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `.env`
- For Docker: `docker-compose ps` should show postgres as "Up"

### Issue 4: dbt Tests Failing

**Symptom**: Some dbt tests show failures

**Solution**:
- This can happen with limited test data
- Check which tests failed: `dbt test`
- View the compiled SQL in `target/compiled/`
- Some tests may need adjustment for your data

### Issue 5: YOLO Download Slow

**Symptom**: YOLOv8 model download takes time

**Solution**:
- First run downloads ~6MB model
- Wait patiently (one-time only)
- Check internet connection
- Model is cached for future runs

## Next Steps

Once everything is running:

1. **Explore the Data**
   - Use dbt docs to understand the models
   - Query the marts tables
   - Try API endpoints

2. **Customize**
   - Add more channels
   - Modify dbt models
   - Add new API endpoints
   - Adjust YOLO thresholds

3. **Schedule**
   - Set up daily runs in Dagster
   - Configure alerts
   - Monitor pipeline health

4. **Deploy**
   - Move to production database
   - Deploy API to server
   - Set up automated backups

## Getting Help

### Documentation
- `README.md` - Project overview
- `SETUP.md` - Detailed setup instructions
- `PROJECT_REPORT.md` - Complete technical report
- `medical_warehouse/README.md` - dbt project docs

### Logs
- `logs/scraper_*.log` - Scraper execution
- `logs/load_raw_*.log` - Data loading
- `logs/yolo_detect_*.log` - YOLO detection
- `medical_warehouse/logs/dbt.log` - dbt runs

### Support Channels
- Slack: #all-week8
- Office Hours: Mon-Fri, 08:00-15:00 UTC
- Tutors: Kerod, Mahbubah, Feven

## Resources

- [Telethon Tutorial](https://docs.telethon.dev/en/stable/basic/quick-start.html)
- [dbt Tutorial](https://docs.getdbt.com/tutorial/learning-more/using-sources)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Dagster Tutorial](https://docs.dagster.io/tutorial)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)

## Submission Checklist

For Interim Submission (June 28):
- [ ] Scraper working and data collected
- [ ] Raw data in PostgreSQL
- [ ] dbt models created and tested
- [ ] Basic documentation
- [ ] GitHub repository

For Final Submission (June 30):
- [ ] Complete pipeline working
- [ ] YOLO integration done
- [ ] API fully functional
- [ ] Dagster orchestration set up
- [ ] Comprehensive documentation
- [ ] Tests passing
- [ ] Final report (blog post format)
- [ ] Screenshots of all components

Good luck with your project! 🚀
