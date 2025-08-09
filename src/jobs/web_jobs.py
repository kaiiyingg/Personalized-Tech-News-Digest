#!/usr/bin/env python3
"""
Web-triggered article ingestion for Render free tier.
This script can be called via HTTP endpoints instead of background scheduling.
"""
import subprocess
import sys
import os
from datetime import datetime
import json

# Add the project root directory to the path to import services
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
from src.services.content_service import cleanup_old_articles

def run_ingest_articles():
    """Run article ingestion job"""
    try:
        print(f"[{datetime.now()}] Starting article ingestion...")
        
        # Import and run the ingestion function directly
        import importlib.util
        import os
        
        spec = importlib.util.spec_from_file_location(
            "ingest_module", 
            os.path.join(os.path.dirname(__file__), "02_ingest_articles.py")
        )
        ingest_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ingest_module)
        
        result = ingest_module.fetch_and_ingest()
        
        return {
            "success": True,
            "message": "Article ingestion completed",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
    except Exception as e:
        print(f"Ingestion error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def run_cleanup():
    """Run cleanup job"""
    try:
        print(f"[{datetime.now()}] Starting cleanup...")
        result = cleanup_old_articles()
        
        return {
            "success": True,
            "message": "Cleanup completed",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
    except Exception as e:
        print(f"Cleanup error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "ingest":
            result = run_ingest_articles()
            print(json.dumps(result, indent=2))
        elif sys.argv[1] == "cleanup":
            result = run_cleanup()
            print(json.dumps(result, indent=2))
        else:
            print("Usage: python web_jobs.py [ingest|cleanup]")
    else:
        print("Usage: python web_jobs.py [ingest|cleanup]")
