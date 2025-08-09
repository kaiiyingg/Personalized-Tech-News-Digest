#!/usr/bin/env python3
"""
Single run article ingestion for testing on Render
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import using module path
import importlib.util
spec = importlib.util.spec_from_file_location("ingest_module", os.path.join(os.path.dirname(__file__), "jobs", "02_ingest_articles.py"))
ingest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_module)

if __name__ == "__main__":
    print("Starting single article ingestion run...")
    try:
        ingest_module.fetch_and_ingest()
        print("Ingestion completed successfully!")
    except Exception as e:
        print(f"Ingestion failed: {e}")
        sys.exit(1)
