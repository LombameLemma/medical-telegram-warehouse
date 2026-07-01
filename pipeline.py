"""
Dagster Pipeline for Medical Telegram Data Warehouse
Orchestrates the end-to-end data pipeline.
"""
import asyncio
import subprocess
import sys
from pathlib import Path

from dagster import (
    op,
    job,
    schedule,
    ScheduleDefinition,
    Definitions,
    OpExecutionContext,
    DagsterRunStatus,
    RunRequest,
    sensor,
    RunConfig,
    AssetKey,
    Output
)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import PROJECT_ROOT


@op(description="Scrape data from Telegram channels")
def scrape_telegram_data(context: OpExecutionContext):
    """
    Run the Telegram scraper to extract messages and images.
    """
    context.log.info("Starting Telegram data scraping...")
    
    try:
        # Run the scraper script
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "scraper.py")],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("Scraper output:")
        context.log.info(result.stdout)
        
        if result.stderr:
            context.log.warning(f"Scraper warnings: {result.stderr}")
        
        context.log.info("Telegram scraping completed successfully")
        return Output(True, metadata={"status": "success"})
    
    except subprocess.CalledProcessError as e:
        context.log.error(f"Scraper failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Error running scraper: {str(e)}")
        raise


@op(description="Load raw JSON data to PostgreSQL")
def load_raw_to_postgres(context: OpExecutionContext, scrape_telegram_data):
    """
    Load raw data from JSON files into PostgreSQL raw schema.
    """
    context.log.info("Loading raw data to PostgreSQL...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "load_raw_data.py")],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("Loader output:")
        context.log.info(result.stdout)
        
        if result.stderr:
            context.log.warning(f"Loader warnings: {result.stderr}")
        
        context.log.info("Raw data loaded successfully")
        return Output(True, metadata={"status": "success"})
    
    except subprocess.CalledProcessError as e:
        context.log.error(f"Loader failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Error loading raw data: {str(e)}")
        raise


@op(description="Run dbt transformations")
def run_dbt_transformations(context: OpExecutionContext, load_raw_to_postgres):
    """
    Execute dbt models to transform data into dimensional schema.
    """
    context.log.info("Running dbt transformations...")
    
    dbt_project_dir = PROJECT_ROOT / "medical_warehouse"
    
    try:
        # Install dbt packages
        context.log.info("Installing dbt packages...")
        subprocess.run(
            ["dbt", "deps"],
            cwd=str(dbt_project_dir),
            check=True,
            capture_output=True,
            text=True
        )
        
        # Run dbt models
        context.log.info("Running dbt models...")
        result = subprocess.run(
            ["dbt", "run"],
            cwd=str(dbt_project_dir),
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("dbt run output:")
        context.log.info(result.stdout)
        
        # Run dbt tests
        context.log.info("Running dbt tests...")
        test_result = subprocess.run(
            ["dbt", "test"],
            cwd=str(dbt_project_dir),
            capture_output=True,
            text=True,
            check=False  # Don't fail pipeline on test failures
        )
        
        context.log.info("dbt test output:")
        context.log.info(test_result.stdout)
        
        if test_result.returncode != 0:
            context.log.warning("Some dbt tests failed - check output above")
        
        context.log.info("dbt transformations completed")
        return Output(True, metadata={"status": "success"})
    
    except subprocess.CalledProcessError as e:
        context.log.error(f"dbt failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Error running dbt: {str(e)}")
        raise


@op(description="Run YOLO object detection on images")
def run_yolo_enrichment(context: OpExecutionContext, scrape_telegram_data):
    """
    Run YOLO object detection on scraped images.
    """
    context.log.info("Running YOLO object detection...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "yolo_detect.py")],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("YOLO output:")
        context.log.info(result.stdout)
        
        if result.stderr:
            context.log.warning(f"YOLO warnings: {result.stderr}")
        
        context.log.info("YOLO detection completed successfully")
        return Output(True, metadata={"status": "success"})
    
    except subprocess.CalledProcessError as e:
        context.log.error(f"YOLO detection failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Error running YOLO: {str(e)}")
        raise


@op(description="Load YOLO results to PostgreSQL")
def load_yolo_results(context: OpExecutionContext, run_yolo_enrichment):
    """
    Load YOLO detection results into PostgreSQL.
    """
    context.log.info("Loading YOLO results to PostgreSQL...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "load_yolo_results.py")],
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("YOLO loader output:")
        context.log.info(result.stdout)
        
        if result.stderr:
            context.log.warning(f"YOLO loader warnings: {result.stderr}")
        
        context.log.info("YOLO results loaded successfully")
        return Output(True, metadata={"status": "success"})
    
    except subprocess.CalledProcessError as e:
        context.log.error(f"YOLO loader failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Error loading YOLO results: {str(e)}")
        raise


@op(description="Rebuild dbt models with YOLO data")
def rebuild_marts_with_yolo(context: OpExecutionContext, load_yolo_results, run_dbt_transformations):
    """
    Rebuild dbt marts to include YOLO enrichment data.
    """
    context.log.info("Rebuilding dbt marts with YOLO data...")
    
    dbt_project_dir = PROJECT_ROOT / "medical_warehouse"
    
    try:
        # Run only the image detections model
        result = subprocess.run(
            ["dbt", "run", "--select", "fct_image_detections"],
            cwd=str(dbt_project_dir),
            capture_output=True,
            text=True,
            check=True
        )
        
        context.log.info("dbt run output:")
        context.log.info(result.stdout)
        
        context.log.info("Marts rebuilt with YOLO data")
        return Output(True, metadata={"status": "success"})
    
    except subprocess.CalledProcessError as e:
        context.log.error(f"dbt rebuild failed: {e.stderr}")
        raise
    except Exception as e:
        context.log.error(f"Error rebuilding marts: {str(e)}")
        raise


@job(description="Complete ETL pipeline for medical telegram data")
def medical_telegram_pipeline():
    """
    Complete pipeline that:
    1. Scrapes Telegram data
    2. Loads raw data to PostgreSQL
    3. Runs dbt transformations
    4. Runs YOLO detection
    5. Loads YOLO results
    6. Rebuilds marts with enrichment
    """
    # Scrape data
    scrape_result = scrape_telegram_data()
    
    # Load raw data (depends on scraping)
    load_result = load_raw_to_postgres(scrape_result)
    
    # Run dbt transformations (depends on loading)
    dbt_result = run_dbt_transformations(load_result)
    
    # Run YOLO (can run in parallel with dbt, depends only on scraping)
    yolo_result = run_yolo_enrichment(scrape_result)
    
    # Load YOLO results (depends on YOLO)
    yolo_load_result = load_yolo_results(yolo_result)
    
    # Rebuild marts with YOLO data (depends on both YOLO load and dbt)
    rebuild_marts_with_yolo(yolo_load_result, dbt_result)


# Schedule to run daily at 2 AM
@schedule(
    job=medical_telegram_pipeline,
    cron_schedule="0 2 * * *",  # 2 AM every day
)
def daily_pipeline_schedule():
    """
    Schedule the pipeline to run daily at 2 AM.
    """
    return RunRequest()


# Alternative: Weekly schedule for less frequent updates
@schedule(
    job=medical_telegram_pipeline,
    cron_schedule="0 2 * * 0",  # 2 AM every Sunday
)
def weekly_pipeline_schedule():
    """
    Schedule the pipeline to run weekly on Sunday at 2 AM.
    """
    return RunRequest()


# Define all assets
defs = Definitions(
    jobs=[medical_telegram_pipeline],
    schedules=[daily_pipeline_schedule, weekly_pipeline_schedule],
)


if __name__ == "__main__":
    # For testing - run the pipeline directly
    result = medical_telegram_pipeline.execute_in_process()
    print(f"Pipeline execution status: {result.success}")
