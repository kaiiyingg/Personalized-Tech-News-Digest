#!/usr/bin/env python3
"""
FAST REFRESH - Optimized Article Ingestion

Ultra-fast refresh mode designed for real-time user experience:
- Only fetch latest 2-3 articles per source
- Skip URL reachability checks for speed
- Parallel processing of feeds
- Smart duplicate detection
"""

import feedparser
import asyncio
import aiohttp
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.database.connection import get_db_connection, close_db_connection
from src.services.content_service import create_content_item
from src.services.source_service import get_all_sources

# FAST MODE CONFIGURATION
FAST_MODE_ARTICLES = 5 
CONCURRENT_FEEDS = 10   
REQUEST_TIMEOUT = 5    
SKIP_URL_VALIDATION = True  # Skip reachability checks for speed

def fetch_feed_fast(source):
    """Fast fetch with minimal processing"""
    try:
        # Quick feedparser fetch with timeout
        feed = feedparser.parse(source.feed_url)
        
        if not feed.entries:
            return {'source_id': source.id, 'articles': 0, 'status': 'no_entries'}
        
        # Take only the newest articles
        recent_entries = feed.entries[:FAST_MODE_ARTICLES]
        articles_added = 0
        
        for entry in recent_entries:
            try:
                # Quick duplicate check
                if is_duplicate_fast(entry.link):
                    continue
                    
                # Create content item with minimal validation
                if create_content_item(
                    title=entry.title,
                    summary=getattr(entry, 'summary', entry.title),
                    url=entry.link,
                    published_at=datetime.now(),  # Use current time for speed
                    source_id=source.id
                ):
                    articles_added += 1
                    
            except Exception as e:
                continue  # Skip individual article errors
        
        return {
            'source_id': source.id, 
            'articles': articles_added, 
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'source_id': source.id, 
            'articles': 0, 
            'status': f'error: {str(e)[:50]}'
        }

def is_duplicate_fast(url):
    """Fast duplicate check using simple URL comparison"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM content WHERE url = %s LIMIT 1", (url,))
        result = cur.fetchone() is not None
        close_db_connection(conn)
        return result
    except:
        return False  # If check fails, allow the article

def fast_refresh():
    """Ultra-fast refresh for real-time user experience"""
    start_time = datetime.now()
    print(f"[FAST REFRESH] Starting at {start_time.isoformat()}")
    
    sources = get_all_sources()
    if not sources:
        return {
            'success': False,
            'error': 'No sources found',
            'duration': 0
        }
    
    total_articles = 0
    results = []
    
    # Process feeds in parallel
    with ThreadPoolExecutor(max_workers=CONCURRENT_FEEDS) as executor:
        future_to_source = {
            executor.submit(fetch_feed_fast, source): source 
            for source in sources
        }
        
        for future in as_completed(future_to_source, timeout=30):
            result = future.result()
            results.append(result)
            total_articles += result['articles']
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"[FAST REFRESH] Completed in {duration:.2f}s - {total_articles} new articles")
    
    return {
        'success': True,
        'articles_added': total_articles,
        'sources_processed': len(sources),
        'duration_seconds': duration,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    result = fast_refresh()
    print(f"Fast refresh result: {result}")
