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
from src.services.source_service import get_all_sources
from bs4 import BeautifulSoup
from src.services.url_validator import is_url_reachable

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
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        new_articles = 0
        sources_in_db = get_all_sources()
        print(f"[Ingestion] Found {len(sources_in_db)} sources in DB.")
        url_to_id = {s.feed_url: s.id for s in sources_in_db}
        if not sources_in_db:
            print("[Ingestion] No sources found in DB. Did sync_sources run?")
        for source in RSS_SOURCES:
            feed_url = source["url"]
            source_id = url_to_id.get(feed_url)
            if not source_id:
                print(f"[Ingestion] Source not found in DB for {feed_url}, skipping.")
                continue
            print(f"[Ingestion] Fetching: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
                print(f"[Ingestion] {feed_url} returned {len(feed.entries)} entries.")
            except Exception as e:
                print(f"[Ingestion] Error parsing feed {feed_url}: {e}")
                continue
            if not feed.entries:
                print(f"[Ingestion] No entries found in feed: {feed_url}")
            for entry in feed.entries:
                try:
                    article_url = str(entry.get("link", ""))
                    title = str(entry.get("title", "No Title"))
                    summary = str(entry.get("summary", ""))
                    published_at = entry.get("published_parsed")
                    if published_at and isinstance(published_at, time.struct_time):
                        published_at = datetime.fromtimestamp(time.mktime(published_at))
                    else:
                        published_at = datetime.now()

                    # --- Enhanced image extraction logic ---
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
                    content = create_content_item(source_id, title, summary, article_url, published_at, image_url=image_url)
                    if content:
                        print(f"[Ingestion] Added article: {title} ({article_url})")
                        new_articles += 1
                    else:
                        print(f"[Ingestion] Failed to add article: {title} ({article_url})")
                except Exception as e:
                    print(f"[Ingestion] Error processing entry in {feed_url}: {e}")
        conn.commit()
        close_db_connection(conn)
        if new_articles == 0:
            print("[Ingestion] No new articles ingested.")
        else:
            print(f"[Ingestion] Finished. {new_articles} new articles added.")
    except Exception as e:
        print(f"[Ingestion] Fatal error: {e}")

# Schedule to run every hour
schedule.every(1).minutes.do(fetch_and_ingest)  # For debugging, run every minute. Change back to hour if it works.

if __name__ == "__main__":
    print("Starting scheduler for article ingestion...")
    fetch_and_ingest()  # Run once at startup
    while True:
        print(f"[Scheduler] Heartbeat: {datetime.now().isoformat()}")
        schedule.run_pending()
        time.sleep(60)
