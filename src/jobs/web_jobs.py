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
    """Run article ingestion job with better error handling and irrelevant content cleanup"""
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
        
        # Run ingestion first
        ingest_result = ingest_module.fetch_and_ingest()
        
        # After ingestion, clean up old articles
        print(f"[{datetime.now()}] Starting cleanup of old articles...")
        cleanup_result = cleanup_old_articles()
        
        return {
            "success": True,
            "message": "Article ingestion and cleanup completed",
            "timestamp": datetime.now().isoformat(),
            "ingest_result": ingest_result,
            "cleanup_result": cleanup_result,
        }
    except ImportError as e:
        print(f"Import error during ingestion: {e}")
        return {
            "success": False,
            "error": f"Module import failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Ingestion error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def run_fast_ingest():
    """Fast refresh mode - optimized for speed"""
    try:
        print(f"[FAST REFRESH] Starting at {datetime.now().isoformat()}")
        
        # Import the fast ingest function
        from .fast_ingest import fast_refresh
        result = fast_refresh()
        
        return {
            "success": True,
            "message": f"Fast refresh completed - {result.get('articles_added', 0)} articles",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
    except Exception as e:
        print(f"Fast refresh error: {e}")
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
