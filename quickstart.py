"""
Quick Start Script for Medical Telegram Warehouse
Helps verify setup and run the pipeline.
"""
import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print welcome banner."""
    print("=" * 70)
    print("   Medical Telegram Data Warehouse - Quick Start")
    print("=" * 70)
    print()

def check_python_version():
    """Check if Python version is adequate."""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"  ✗ Python {version.major}.{version.minor} detected")
        print("  ! Python 3.9+ required")
        return False
    print(f"  ✓ Python {version.major}.{version.minor} - OK")
    return True

def check_env_file():
    """Check if .env file exists."""
    print("✓ Checking environment configuration...")
    env_file = Path(".env")
    if not env_file.exists():
        print("  ✗ .env file not found")
        print("  ! Please copy .env.example to .env and fill in your credentials")
        return False
    print("  ✓ .env file exists")
    
    # Check if critical vars are set
    from dotenv import load_dotenv
    load_dotenv()
    
    critical_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'DB_PASSWORD']
    missing = []
    for var in critical_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"  ⚠ Missing environment variables: {', '.join(missing)}")
        print("  ! Please update .env file")
        return False
    
    print("  ✓ Critical environment variables set")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    print("✓ Checking dependencies...")
    try:
        import telethon
        import psycopg2
        import sqlalchemy
        import fastapi
        import ultralytics
        import dagster
        print("  ✓ All core dependencies installed")
        return True
    except ImportError as e:
        print(f"  ✗ Missing dependency: {e.name}")
        print("  ! Run: pip install -r requirements.txt")
        return False

def check_database():
    """Check if database is accessible."""
    print("✓ Checking database connection...")
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'medical_warehouse'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        conn.close()
        print("  ✓ Database connection successful")
        return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {str(e)}")
        print("  ! Make sure PostgreSQL is running and credentials are correct")
        return False

def check_directories():
    """Create necessary directories."""
    print("✓ Creating project directories...")
    directories = [
        "data/raw/telegram_messages",
        "data/raw/images",
        "data/processed",
        "logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("  ✓ All directories created")
    return True

def run_setup():
    """Run complete setup check."""
    print_banner()
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("Directories", check_directories),
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
        print()
    
    if all_passed:
        print("=" * 70)
        print("✓ All checks passed! You're ready to run the pipeline.")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Update channel usernames in src/config.py")
        print("  2. Run the pipeline manually:")
        print("     - python src/scraper.py")
        print("     - python src/load_raw_data.py")
        print("     - cd medical_warehouse && dbt run && cd ..")
        print("  3. Or use Dagster: dagster dev -f pipeline.py")
        print("  4. Start the API: uvicorn api.main:app --reload")
        print()
    else:
        print("=" * 70)
        print("✗ Some checks failed. Please fix the issues above.")
        print("=" * 70)
        print()
        print("For detailed setup instructions, see SETUP.md")
        print()

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        print("Running full pipeline...")
        # This would run the actual pipeline
        print("Feature coming soon - use Dagster for now")
    else:
        run_setup()

if __name__ == "__main__":
    main()
