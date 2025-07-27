#!/usr/bin/env python3
"""
Scheduler for automated jobs: sync sources and ingest articles.
Runs sync_sources daily and ingest_articles hourly.
"""
import schedule
import time
import subprocess
import os

JOBS_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths to job scripts
SYNC_SOURCES = os.path.join(JOBS_DIR, "01_sync_sources.py")
INGEST_ARTICLES = os.path.join(JOBS_DIR, "02_ingest_articles.py")


def run_sync_sources():
    subprocess.run(["python", SYNC_SOURCES])

def run_ingest_articles():
    subprocess.run(["python", INGEST_ARTICLES])

# Schedule jobs
schedule.every().day.at("00:00").do(run_sync_sources)
schedule.every().hour.do(run_ingest_articles)

if __name__ == "__main__":
    print("Scheduler started. Running jobs as scheduled...")
    while True:
        schedule.run_pending()
        time.sleep(60)
