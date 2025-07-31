#!/usr/bin/env python3
"""
TechPulse Scheduler:

- Hourly article ingestion from all sources in your database
- Daily cleanup of old articles at 3:00 AM (favorites are always preserved)

Note: RSS source synchronization is now manual. Run the sync_sources script yourself if you want to add/remove sources.
"""
import schedule
import time
import subprocess
import os
from datetime import datetime

JOBS_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to ingestion job script
INGEST_ARTICLES = os.path.join(JOBS_DIR, "02_ingest_articles.py")

# Import cleanup function from services/content_service
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.content_service import cleanup_old_articles



def run_ingest_articles():
    print(f"[{datetime.now()}] ingest_articles job started.")
    subprocess.run([sys.executable, "-m", "src.jobs.02_ingest_articles"])


def run_daily_cleanup():
    print(f"[{datetime.now()}] daily_cleanup job started.")
    try:
        result = cleanup_old_articles()
        if 'error' in result:
            print(f"Cleanup failed: {result['error']}")
        else:
            print(f"Cleanup completed: {result.get('action_taken', 'unknown')}, Deleted: {result.get('deleted_count', 0)}, Reason: {result.get('reason', 'N/A')}")
    except Exception as e:
        print(f"Cleanup job error: {e}")

def start_scheduler():
    print("TechPulse Unified Scheduler Starting...")
    print("Ingest articles hourly")
    print("Cleanup old articles daily at 03:00 (preserving favorites)")

    # Automate ingestion and cleanup
    schedule.every().hour.do(run_ingest_articles)
    schedule.every().day.at("03:00").do(run_daily_cleanup)

    print("Scheduler active. Waiting for next scheduled job...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    try:
        start_scheduler()
    except KeyboardInterrupt:
        print("Scheduler stopped by user")
    except Exception as e:
        print(f"Scheduler error: {e}")
