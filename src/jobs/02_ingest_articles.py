#!/usr/bin/env python3
"""
TechPulse Article Ingestion Script (On-Demand)

This script fetches and ingests new articles from all RSS sources in your database.
It is designed to be triggered on-demand via web interface for user-driven content updates.

Key points:
- This script does NOT manage the list of RSS sources. To add/remove sources, run the sync_sources script manually.
- Ingestion will only use sources currently in your database.
- Avoids duplicates, skips unreachable URLs, and only ingests tech-related articles.
- Optimized for user-driven updates rather than background scheduling.

Usage:
    python -m src.jobs.02_ingest_articles
    Or call fetch_and_ingest() function directly from web endpoints.
"""


import feedparser
import time
from datetime import datetime, timedelta
from src.database.connection import get_db_connection, close_db_connection
from src.services.content_service import create_content_item
from src.services.source_service import get_all_sources
from bs4 import BeautifulSoup
from src.services.url_validator import is_url_reachable

# Constants for HTML cleaning and parsing
HTML_PARSER = "html.parser"
HTML_TAG_PATTERN = r'<[^>]+>'
HTML_ENTITY_PATTERN = r'&[a-zA-Z0-9#]+;'

# Configuration for comprehensive content refresh
# Increased articles per feed since AI processing is disabled for memory optimization
MAX_ARTICLES_PER_FEED = 10  # Increased to 10 for comprehensive coverage without AI memory overhead

# Memory optimization: Disable AI processing for 512MB memory limit
USE_AI_PROCESSING = False  # Set to False to avoid memory issues on free tier

def cleanup_old_articles(days_to_keep=30):
    """Remove articles older than specified days to keep database manageable"""
    print(f"[Cleanup] Removing articles older than {days_to_keep} days...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Get count before cleanup
        cur.execute("SELECT COUNT(*) FROM content WHERE published_at < %s", (cutoff_date,))
        old_count = cur.fetchone()[0]
        
        if old_count > 0:
            print(f"[Cleanup] Found {old_count} articles older than {cutoff_date.strftime('%Y-%m-%d')}")
            
            # Remove old articles (preserve user interactions by using CASCADE or handling separately)
            cur.execute("DELETE FROM content WHERE published_at < %s", (cutoff_date,))
            conn.commit()
            
            print(f"[Cleanup] ✅ Removed {old_count} old articles")
        else:
            print("[Cleanup] ✅ No old articles to remove")
            
        # Get total remaining articles
        cur.execute("SELECT COUNT(*) FROM content")
        remaining_count = cur.fetchone()[0]
        print(f"[Cleanup] 📊 Database now contains {remaining_count} articles")
        
        close_db_connection(conn)
        return True
        
    except Exception as e:
        print(f"[Cleanup] ❌ Error during cleanup: {e}")
        return False

## NOTE: RSS_SOURCES is not used for ingestion. The script fetches sources from your database.


def fetch_and_ingest():
    print(f"[Ingestion] Starting at {datetime.now().isoformat()}")
    
    # Step 1: Clean up old articles first
    if not cleanup_old_articles(days_to_keep=30):
        print("[Ingestion] ⚠️  Cleanup failed, continuing with ingestion...")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        new_articles = 0
        sources_in_db = get_all_sources()
        print(f"[Ingestion] Found {len(sources_in_db)} sources in DB.")
        if not sources_in_db:
            print("[Ingestion] No sources found in DB. Did sync_sources run?")
        # --- Round-robin ingestion: 1 article per source per round ---
        # Step 1: Parse all feeds and collect entries per source
        feeds = []  # List of dicts: { 'source_id': ..., 'entries': [...], 'feed_url': ... }
        for source in sources_in_db:
            feed_url = source.feed_url
            source_id = source.id
            print(f"[Ingestion] Fetching: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
                print(f"[Ingestion] {feed_url} returned {len(feed.entries)} entries.")
                # Limit entries for faster refresh - take only the most recent ones
                limited_entries = list(feed.entries)[:MAX_ARTICLES_PER_FEED]
                print(f"[Ingestion] Processing {len(limited_entries)} most recent entries for speed optimization.")
                feeds.append({"source_id": source_id, "entries": limited_entries, "feed_url": feed_url})
            except Exception as e:
                print(f"[Ingestion] Error parsing feed {feed_url}: {e}")
                continue

        # Step 2: Ingest in round-robin fashion
        round_idx = 0
        while True:
            any_added_this_round = False
            for feed in feeds:
                entries = feed["entries"]
                source_id = feed["source_id"]
                feed_url = feed["feed_url"]
                if round_idx < len(entries):
                    entry = entries[round_idx]
                    try:
                        article_url = str(entry.get("link", ""))
                        title = str(entry.get("title", "No Title"))
                        # Use full content for summarization if available, else fallback to summary
                        article_text = ""
                        if hasattr(entry, "content") and entry.content:
                            # Some feeds provide full content in entry.content
                            for c in entry.content:
                                html = c.get("value") if isinstance(c, dict) else None
                                if html:
                                    soup = BeautifulSoup(html, HTML_PARSER)
                                    article_text = soup.get_text(separator=" ", strip=True)
                                    break
                        if not article_text:
                            # Fallback to summary from RSS feed, but clean it first
                            raw_summary = str(entry.get("summary", ""))
                            if raw_summary:
                                # Clean HTML tags from RSS summary
                                soup = BeautifulSoup(raw_summary, "html.parser")
                                article_text = soup.get_text(separator=" ", strip=True)
                            else:
                                article_text = title
                        
                        # Memory optimization: Skip AI processing to stay within 512MB limit
                        # Create a simple excerpt from the article text
                        import re
                        
                        # Clean the text and create an excerpt
                        clean_text = re.sub(HTML_TAG_PATTERN, '', article_text)  # Remove HTML tags
                        clean_text = re.sub(HTML_ENTITY_PATTERN, ' ', clean_text)  # Remove HTML entities
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Clean up whitespace
                        
                        # Create excerpt: first 200 characters or first complete sentence
                        if len(clean_text) > 200:
                            excerpt = clean_text[:200]
                            # Try to end at a sentence boundary
                            last_period = excerpt.rfind('.')
                            if last_period > 100:  # Only use sentence boundary if it's not too short
                                excerpt = excerpt[:last_period + 1]
                            else:
                                excerpt += "..."
                        else:
                            excerpt = clean_text
                        
                        summary = excerpt
                        published_at = entry.get("published_parsed")
                        if published_at and isinstance(published_at, time.struct_time):
                            published_at = datetime.fromtimestamp(time.mktime(published_at))
                        else:
                            published_at = datetime.now()

                        # --- Enhanced image extraction logic (same as before) ---
                        image_url = None
                        from bs4.element import Tag
                        def is_valid_img_url(url):
                            return isinstance(url, str) and url.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))

                        # 1. media_content
                        if hasattr(entry, "media_content") and entry.media_content:
                            for media in entry.media_content:
                                url = media.get("url") if isinstance(media, dict) else None
                                if is_valid_img_url(url):
                                    image_url = url
                                    break
                        # 2. media_thumbnail
                        if not image_url and hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                            for thumb in entry.media_thumbnail:
                                url = thumb.get("url") if isinstance(thumb, dict) else None
                                if is_valid_img_url(url):
                                    image_url = url
                                    break
                        # 3. enclosures
                        if not image_url and hasattr(entry, "enclosures") and entry.enclosures:
                            for enc in entry.enclosures:
                                url = enc.get("href") if isinstance(enc, dict) else None
                                if is_valid_img_url(url):
                                    image_url = url
                                    break
                        # 4. entry.image
                        if not image_url and hasattr(entry, "image") and isinstance(entry.image, dict):
                            url = entry.image.get("href")
                            if is_valid_img_url(url):
                                image_url = url

                        # 5. Extract from summary/content HTML
                        def extract_img_from_html(html):
                            soup = BeautifulSoup(html, "html.parser")
                            imgs = soup.find_all("img")
                            candidates = []
                            for img in imgs:
                                if isinstance(img, Tag) and img.has_attr("src"):
                                    src = img.get("src")
                                    if src and isinstance(src, str) and is_valid_img_url(src):
                                        if not any(x in src.lower() for x in ["logo", "icon", "sprite", "spacer", "blank", "pixel", "1x1", "tracking"]):
                                            candidates.append(img)
                            if candidates:
                                def get_area(img):
                                    try:
                                        w = int(img.get("width", 0))
                                        h = int(img.get("height", 0))
                                        return w * h
                                    except Exception:
                                        return 0
                                candidates.sort(key=get_area, reverse=True)
                                return candidates[0].get("src")
                            return None

                        if not image_url and summary:
                            img_from_summary = extract_img_from_html(summary)
                            if img_from_summary:
                                image_url = img_from_summary
                        if not image_url and hasattr(entry, "content") and entry.content:
                            for c in entry.content:
                                html = c.get("value") if isinstance(c, dict) else None
                                if html:
                                    img_from_content = extract_img_from_html(html)
                                    if img_from_content:
                                        image_url = img_from_content
                                        break

                        # 6. Open Graph/Twitter meta tags in summary HTML
                        if not image_url and summary:
                            soup = BeautifulSoup(summary, "html.parser")
                            og_img = soup.find("meta", property="og:image")
                            if og_img and isinstance(og_img, Tag):
                                content_val = og_img.get("content")
                                if is_valid_img_url(content_val):
                                    image_url = content_val
                            twitter_img = soup.find("meta", property="twitter:image")
                            if twitter_img and isinstance(twitter_img, Tag):
                                content_val = twitter_img.get("content")
                                if is_valid_img_url(content_val):
                                    image_url = content_val

                        # 7. Fallback: first image found anywhere
                        if not image_url and summary:
                            soup = BeautifulSoup(summary, "html.parser")
                            img_tag = soup.find("img")
                            if img_tag and isinstance(img_tag, Tag) and img_tag.has_attr("src"):
                                src = img_tag.get("src")
                                if is_valid_img_url(src):
                                    image_url = src

                        # Ensure string type
                        if isinstance(image_url, list):
                            image_url = image_url[0] if image_url else None
                        if image_url is not None and not isinstance(image_url, str):
                            image_url = str(image_url)

                        # Assign topic and filter out non-tech articles
                        from src.services.content_service import assign_topic
                        topic = assign_topic(title, summary)
                        if topic == "Other":
                            print(f"[Ingestion] Skipping non-tech article: {title}")
                            continue
                        print(f"[Ingestion] Checking for duplicate: {article_url}")
                        cur.execute("SELECT id FROM content WHERE article_url = %s", (article_url,))
                        if cur.fetchone():
                            print(f"[Ingestion] Duplicate found, skipping: {article_url}")
                            continue
                        # Validate URL before saving
                        if not is_url_reachable(article_url):
                            print(f"[Ingestion] URL not reachable, skipping: {article_url}")
                            continue
                        print(f"[Ingestion] Inserting article: {title} ({article_url})")
                        content = create_content_item(source_id, title, summary, article_url, published_at, topic=topic, image_url=image_url)
                        if content:
                            print(f"[Ingestion] Added article: {title} ({article_url})")
                            new_articles += 1
                            any_added_this_round = True
                        else:
                            print(f"[Ingestion] Failed to add article: {title} ({article_url})")
                    except Exception as e:
                        print(f"[Ingestion] Error processing entry in {feed_url}: {e}")
            # End for feed in feeds
            if not any_added_this_round:
                break  # No more articles to add in any feed
            round_idx += 1
        conn.commit()
        close_db_connection(conn)
        if new_articles == 0:
            print("[Ingestion] No new articles ingested.")
        else:
            print(f"[Ingestion] Finished. {new_articles} new articles added.")
    except Exception as e:
        print(f"[Ingestion] Fatal error: {e}")
        return {"success": False, "error": str(e)}
    
    return {"success": True, "articles_added": new_articles}

if __name__ == "__main__":
    print("🚀 TechPulse On-Demand Article Ingestion")
    print("=" * 50)
    print(" Features:")
    print("   • Strict tech content filtering")
    print("   • AI-powered topic classification")
    print("   • Automatic HTML cleaning")
    print("   • Image extraction")
    print("   • Inappropriate content rejection")
    print("=" * 50)
    
    # Run single ingestion
    result = fetch_and_ingest()
    
    if result.get("success"):
        print(f"✅ Ingestion completed successfully! Added {result.get('articles_added', 0)} new articles.")
    else:
        print(f"❌ Ingestion failed: {result.get('error', 'Unknown error')}")
