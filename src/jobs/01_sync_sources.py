#!/usr/bin/env python3
"""
Sync RSS sources to the database.
X automated using schedular.py so if want to add/remove sources, run this script manually.
Command 'python -m src.jobs.01_sync_sources' for update.
"""

from src.services.source_service import create_source, delete_source, get_all_sources

# List of RSS sources to sync
RSS_SOURCES = [
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
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

def sync_sources():
    # Get current sources from database
    current_sources = get_all_sources()
    current_urls = {s.feed_url: s for s in current_sources}
    target_urls = {s['url']: s for s in RSS_SOURCES}

    # Remove sources not in RSS_SOURCES
    for url, source in current_urls.items():
        if url not in target_urls:
            delete_source(source.id)

    # Add new sources from RSS_SOURCES
    for source in RSS_SOURCES:
        create_source(name=source['name'], feed_url=source['url'])

if __name__ == "__main__":
    sync_sources()
