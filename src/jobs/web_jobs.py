"""
Web job wrappers for HTTP-triggered job endpoints.

This module provides thin wrappers used by app routes so ingestion/cleanup
can be triggered safely and return consistent JSON-serializable payloads.
"""

from datetime import datetime
from typing import Any, Dict

from src.jobs.ingest_articles import fetch_and_ingest
from src.services.content_service import cleanup_old_articles


def run_ingest_articles() -> Dict[str, Any]:
    """Run article ingestion and return a normalized response payload."""
    try:
        result = fetch_and_ingest()
        if not isinstance(result, dict):
            return {
                "success": False,
                "error": "Ingestion returned unexpected response format",
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "success": bool(result.get("success", False)),
            "articles_added": int(result.get("articles_added", 0) or 0),
            "error": result.get("error"),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
        }


def run_cleanup() -> Dict[str, Any]:
    """Run smart cleanup and return a normalized response payload."""
    try:
        cleanup_result = cleanup_old_articles()

        # cleanup_old_articles returns a dict with action details and optional error.
        if isinstance(cleanup_result, dict) and cleanup_result.get("error"):
            return {
                "success": False,
                "error": cleanup_result.get("error"),
                "result": cleanup_result,
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "success": True,
            "result": cleanup_result,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
        }
