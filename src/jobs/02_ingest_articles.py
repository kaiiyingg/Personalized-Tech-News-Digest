#!/usr/bin/env python3
"""
Hourly Article Ingestion Script for TechPulse

- Fetches articles from all RSS sources
- Inserts new articles into Supabase/PostgreSQL
- Avoids duplicates
- Can be scheduled to run every hour using Python's schedule library
"""

import feedparser
import schedule
import time
from datetime import datetime
from src.database.connection import get_db_connection, close_db_connection
from src.services.content_service import create_content_item
from bs4 import BeautifulSoup

# ADD YOUR RSS SOURCES HERE
RSS_SOURCES = [
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss"},
    {"name": "TechRadar", "url": "https://www.techradar.com/rss"},
    {"name": "ZDNet", "url": "https://www.zdnet.com/news/rss.xml"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/"},
    {"name": "Engadget", "url": "https://www.engadget.com/rss.xml"},
    {"name": "9to5Mac", "url": "https://9to5mac.com/feed/"},
    {"name": "Android Police", "url": "https://www.androidpolice.com/feed/"},
    {"name": "Mashable Tech", "url": "https://mashable.com/feeds/rss/all"},
    {"name": "CNET", "url": "https://www.cnet.com/rss/news/"},
    {"name": "IEEE Spectrum", "url": "https://spectrum.ieee.org/rss/fulltext"},
    {"name": "NYT Technology", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"},
    {"name": "Gizmodo", "url": "https://gizmodo.com/feed"},
    {"name": "CNA Tech News", "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416"},
    {"name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "KrebsOnSecurity", "url": "https://krebsonsecurity.com/feed/"},
    {"name": "Dark Reading", "url": "https://www.darkreading.com/rss.xml"},
    {"name": "GitHub Blog", "url": "https://github.blog/feed/"},
    {"name": "Stack Overflow Blog", "url": "https://stackoverflow.blog/feed/"},
    {"name": "Dev.to", "url": "https://dev.to/feed"},
    {"name": "Opensource.com", "url": "https://opensource.com/feed"},
    {"name": "KDnuggets", "url": "https://www.kdnuggets.com/feed"},
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "EFF Deeplinks", "url": "https://www.eff.org/rss/updates.xml"},
]


def fetch_and_ingest():
    print(f"[Ingestion] Starting at {datetime.now().isoformat()}")
    conn = get_db_connection()
    cur = conn.cursor()
    new_articles = 0
    # Build a mapping from feed_url to source_id using the DB
    from services.source_service import get_all_sources
    sources_in_db = get_all_sources()
    url_to_id = {s.feed_url: s.id for s in sources_in_db}

    for source in RSS_SOURCES:
        feed_url = source["url"]
        source_id = url_to_id.get(feed_url)
        if not source_id:
            print(f"Source not found in DB for {feed_url}, skipping.")
            continue
        print(f"Fetching: {feed_url}")
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            article_url = str(entry.get("link", ""))
            title = str(entry.get("title", "No Title"))
            summary = str(entry.get("summary", ""))
            published_at = entry.get("published_parsed")
            if published_at and isinstance(published_at, time.struct_time):
                published_at = datetime.fromtimestamp(time.mktime(published_at))
            else:
                published_at = datetime.now()
            # Extract image_url from entry
            image_url = None
            # Try media_content (list of dicts)
            if hasattr(entry, "media_content") and entry.media_content:
                first_media = entry.media_content[0]
                if isinstance(first_media, dict):
                    image_url = first_media.get("url")
                elif hasattr(first_media, "get"):
                    image_url = first_media.get("url")
            # Try image (dict)
            elif hasattr(entry, "image") and isinstance(entry.image, dict):
                image_url = entry.image.get("href")
            # Try summary HTML
            elif summary:
                soup = BeautifulSoup(summary, "html.parser")
                img_tag = soup.find("img")
                from bs4.element import Tag
                if img_tag and isinstance(img_tag, Tag) and img_tag.has_attr("src"):
                    image_url = img_tag["src"]
            # Ensure image_url is a string
            if isinstance(image_url, list):
                image_url = image_url[0] if image_url else None
            if image_url is not None and not isinstance(image_url, str):
                image_url = str(image_url)
            cur.execute("SELECT id FROM content WHERE article_url = %s", (article_url,))
            if cur.fetchone():
                continue
            content = create_content_item(source_id, title, summary, article_url, published_at, image_url=image_url)
            if content:
                new_articles += 1
    conn.commit()
    close_db_connection(conn)
    print(f"[Ingestion] Finished. {new_articles} new articles added.")

# Schedule to run every hour
schedule.every().hour.do(fetch_and_ingest)

if __name__ == "__main__":
    print("Starting hourly article ingestion...")
    fetch_and_ingest()  # Run once at startup
    while True:
        schedule.run_pending()
        time.sleep(60)
