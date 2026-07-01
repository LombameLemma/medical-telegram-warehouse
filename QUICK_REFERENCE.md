# Quick Reference Card

## 🚀 One-Command Setup

```bash
# Windows
python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt

# Linux/Mac
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

## 📁 Essential Files

| File | Purpose |
|------|---------|
| `src/scraper.py` | Scrape Telegram data |
| `src/load_raw_data.py` | Load JSON → PostgreSQL |
| `src/yolo_detect.py` | Detect objects in images |
| `medical_warehouse/` | dbt transformation project |
| `api/main.py` | FastAPI application |
| `pipeline.py` | Dagster orchestration |

## ⚙️ Configuration

```bash
# 1. Copy environment template
copy .env.example .env

# 2. Edit .env and set:
TELEGRAM_API_ID=your_id
TELEGRAM_API_HASH=your_hash
TELEGRAM_PHONE=+251...
DB_PASSWORD=your_password

# 3. Update channels in src/config.py
```

## 🔄 Manual Pipeline Execution

```bash
# Step 1: Scrape
python src\scraper.py

# Step 2: Load Raw
python src\load_raw_data.py

# Step 3: Transform (dbt)
cd medical_warehouse
dbt run && dbt test
cd ..

# Step 4: YOLO
python src\yolo_detect.py
python src\load_yolo_results.py

# Step 5: Rebuild marts
cd medical_warehouse
dbt run --select fct_image_detections
cd ..

# Step 6: Start API
uvicorn api.main:app --reload
```

## 🤖 Automated Pipeline (Dagster)

```bash
# Start Dagster UI
dagster dev -f pipeline.py

# Open: http://localhost:3000
# Click: Launchpad → Launch Run
```

## 🐘 Database Commands

```sql
-- Connect
psql -U postgres -d medical_warehouse

-- Check data
SELECT COUNT(*) FROM raw.telegram_messages;
SELECT COUNT(*) FROM marts.fct_messages;
SELECT * FROM marts.dim_channels;

-- Quit
\q
```

## 📊 dbt Commands

```bash
cd medical_warehouse

# Install packages
dbt deps

# Run models
dbt run

# Run tests
dbt test

# Generate docs
dbt docs generate
dbt docs serve

# Run specific model
dbt run --select dim_channels

cd ..
```

## 🌐 API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List channels
curl http://localhost:8000/api/channels

# Top products
curl http://localhost:8000/api/reports/top-products?limit=10

# Search messages
curl http://localhost:8000/api/search/messages?query=medicine

# Channel activity
curl http://localhost:8000/api/channels/CheMed123/activity

# Visual content stats
curl http://localhost:8000/api/reports/visual-content

# API Documentation
# http://localhost:8000/docs
```

## 🧪 Testing Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=api --cov=src

# Run specific test
pytest tests/test_api.py::test_health_endpoint_success -v

# dbt tests
cd medical_warehouse && dbt test && cd ..
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Start PostgreSQL only
docker-compose up -d postgres

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild images
docker-compose build --no-cache
```

## 📝 Logging Locations

```
logs/scraper_*.log       - Scraper execution
logs/load_raw_*.log      - Data loading
logs/yolo_detect_*.log   - YOLO detection
medical_warehouse/logs/  - dbt runs
```

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | `pip install -r requirements.txt` |
| DB connection | Check PostgreSQL running, verify .env |
| Telegram auth | Delete .session file, re-authenticate |
| dbt errors | `cd medical_warehouse && dbt debug` |
| YOLO slow | First run downloads model (~6MB) |
| No data | Verify channel usernames are correct |

## 📚 Documentation Map

```
README.md              → Project overview
GETTING_STARTED.md     → Quick start (30 min)
SETUP.md               → Detailed setup
PROJECT_REPORT.md      → Technical report (for submission)
PROJECT_STRUCTURE.md   → File listing
FINAL_CHECKLIST.md     → Submission checklist
```

## 🎯 Task Locations

```
Task 1 (Scraping)       → src/scraper.py
Task 2 (dbt)            → medical_warehouse/models/
Task 3 (YOLO)           → src/yolo_detect.py
Task 4 (API)            → api/main.py
Task 5 (Orchestration)  → pipeline.py
```

## 📊 Data Flow

```
Telegram → scraper.py → data/raw/*.json
         → load_raw_data.py → raw.telegram_messages
         → dbt run → marts.*
         
Images   → yolo_detect.py → yolo_detections.csv
         → load_yolo_results.py → raw.yolo_detections
         → dbt run → fct_image_detections
```

## 🔗 Important URLs

```
API Documentation:    http://localhost:8000/docs
API ReDoc:            http://localhost:8000/redoc
dbt Documentation:    http://localhost:8080 (after dbt docs serve)
Dagster UI:           http://localhost:3000
PostgreSQL:           localhost:5432
```

## 🎓 Learning Resources

```
Telethon:  https://docs.telethon.dev/
dbt:       https://docs.getdbt.com/
FastAPI:   https://fastapi.tiangolo.com/
YOLOv8:    https://docs.ultralytics.com/
Dagster:   https://docs.dagster.io/
```

## 📞 Support

```
Slack:        #all-week8
Office Hours: Mon-Fri, 08:00-15:00 UTC
Tutors:       Kerod, Mahbubah, Feven
```

## ⏰ Key Dates

```
Challenge Intro:    June 24, 2026
Interim Deadline:   June 28, 2026, 8:00 PM UTC
Final Deadline:     June 30, 2026, 8:00 PM UTC
```

## ✅ Pre-Submission Quick Check

```bash
# 1. Verify setup
python quickstart.py

# 2. Run pipeline manually (all steps)
# 3. Start API and test endpoints
# 4. Run dbt tests
cd medical_warehouse && dbt test && cd ..

# 5. Check git status
git status

# 6. Verify no secrets
git grep -i "password"
git grep -i "api_key"

# 7. Create final report with screenshots
```

## 🎉 Success Indicators

✅ `python quickstart.py` shows all green  
✅ Data in `data/raw/` directories  
✅ PostgreSQL has data in all tables  
✅ `dbt test` shows 0 failures  
✅ API `/docs` page loads  
✅ Dagster UI shows pipeline  
✅ All documentation complete  
✅ GitHub repo has all files  

---

**Print this page for quick reference while working!**
