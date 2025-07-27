#!/usr/bin/env python3
"""
TechPulse Scheduler:

- Daily RSS source synchronization (midnight)
- Hourly article ingestion from all sources
- Daily cleanup of old articles at 3:00 AM (favorites are always preserved)
"""
import schedule
import time
import subprocess
import os
from datetime import datetime

JOBS_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths to job scripts
SYNC_SOURCES = os.path.join(JOBS_DIR, "01_sync_sources.py")
INGEST_ARTICLES = os.path.join(JOBS_DIR, "02_ingest_articles.py")

# Import cleanup function from services/content_service
from services.content_service import cleanup_old_articles

def run_sync_sources():
    print(f"[{datetime.now()}] sync_sources job started.")
    subprocess.run(["python", SYNC_SOURCES])

def run_ingest_articles():
    print(f"[{datetime.now()}] ingest_articles job started.")
    subprocess.run(["python", INGEST_ARTICLES])

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
    print("Sync sources now and daily at 00:00")
    print("Ingest articles hourly")
    print("Cleanup old articles daily at 03:00 (preserving favorites)")

    # Always sync sources on startup before any ingestion
    run_sync_sources()

    schedule.every().day.at("00:00").do(run_sync_sources)
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
