#!/usr/bin/env python3
"""
TechPulse Article Ingestion Script (Automated)

This script fetches and ingests new articles from all RSS sources in your database.
It is designed to be run automatically via a scheduler to keep your tech news feed up to date.

Key points:
- This script does NOT manage the list of RSS sources. To add/remove sources, run the sync_sources script manually.
- Ingestion will only use sources currently in your database.
- Avoids duplicates, skips unreachable URLs, and only ingests tech-related articles.
- Can be scheduled to run every hour (or as desired) using Python's schedule library or an external scheduler.

Usage (manual run for testing):
    python -m src.jobs.02_ingest_articles

For automation, set up a scheduler to run this script as needed.
"""


import feedparser
import schedule
import time
from datetime import datetime
from src.database.connection import get_db_connection, close_db_connection
from src.services.content_service import create_content_item
from src.services.source_service import get_all_sources
from bs4 import BeautifulSoup
from src.services.url_validator import is_url_reachable
# Summarization imports
from transformers.pipelines import pipeline
from transformers import AutoTokenizer
summarizer = pipeline("summarization", model="t5-small")
tokenizer = AutoTokenizer.from_pretrained("t5-small")

# Helper to truncate input to 512 tokens for t5-small
def truncate_text(text, tokenizer, max_tokens=512):
    tokens = tokenizer.encode(text, truncation=True, max_length=max_tokens)
    return tokenizer.decode(tokens, skip_special_tokens=True)

## NOTE: RSS_SOURCES is not used for ingestion. The script fetches sources from your database.


def fetch_and_ingest():
    print(f"[Ingestion] Starting at {datetime.now().isoformat()}")
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
                feeds.append({"source_id": source_id, "entries": list(feed.entries), "feed_url": feed_url})
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
                                    soup = BeautifulSoup(html, "html.parser")
                                    article_text = soup.get_text(separator=" ", strip=True)
                                    break
                        if not article_text:
                            # Fallback to summary or title
                            article_text = str(entry.get("summary", "")) or title
                        # Truncate input to 512 tokens for t5-small
                        truncated_text = truncate_text(article_text, tokenizer)
                        # Generate summary using Hugging Face summarizer
                        try:
                            summary = summarizer(truncated_text, max_length=80, min_length=20, do_sample=False)[0]['summary_text']
                        except Exception as e:
                            print(f"[Ingestion] Summarization failed for article '{title}': {e}")
                            summary = truncated_text[:200]  # fallback: truncate
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

# Schedule to run every hour
schedule.every(60).minutes.do(fetch_and_ingest)  

if __name__ == "__main__":
    print("Starting scheduler for article ingestion...")
    fetch_and_ingest()  # Run once at startup
    while True:
        print(f"[Scheduler] Heartbeat: {datetime.now().isoformat()}")
        schedule.run_pending()
        time.sleep(60)
