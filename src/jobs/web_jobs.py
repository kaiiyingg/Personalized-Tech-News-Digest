"""
Web-triggered job wrappers for article ingestion and cleanup.

These functions are called from app.py HTTP endpoints so that
background jobs can be triggered via HTTP on Render's free tier
(which does not support persistent background processes).
"""

from datetime import datetime
from src.jobs.ingest_articles import fetch_and_ingest, cleanup_old_articles


def run_ingest_articles():
    """
    Run the article ingestion job.

    Returns a dict with at least a 'success' key and a 'timestamp' key.
    On success also includes 'articles_added'.
    On failure includes 'error'.
    """
    try:
        result = fetch_and_ingest()
        return {**result, 'timestamp': result.get('timestamp', datetime.now().isoformat())}
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def run_cleanup(days_to_keep=30):
    """
    Run the old-article cleanup job.

    Returns a dict with at least a 'success' key and a 'timestamp' key.
    On failure includes 'error'.
    """
    try:
        success = cleanup_old_articles(days_to_keep=days_to_keep)
        return {
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
