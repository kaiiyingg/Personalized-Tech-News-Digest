#!/usr/bin/env python3
"""
Script to synchronize RSdef sync_sources():
    # NOTE: RSS sources should be global (shared by all users), not user-specific
    # Currently using user_id=1 as workaround until schema is refactored to make sources global
    user_id = 1  # Temporary: storing global sources under user_id=1
    
    print("🔄 Starting RSS source synchronization...")
    print(f"📊 Target sources to sync: {len(RSS_SOURCES)}")
    print("💡 Note: RSS sources are global and shared by all users")
    print("-" * 60)es with the database.

This script ensures the database contains EXACTLY the sources listed in RSS_SOURCES:
- Removes any sources from the database that are NOT in RSS_SOURCES
- Adds any new sources from RSS_SOURCES that are missing from the database

Instructions:
1. Update the RSS_SOURCES list below with your desired sources
2. Run: python add_sources.py
3. The script will sync the database to match RSS_SOURCES exactly
"""

import sys
import os
from src.services.source_service import create_source

# Add the project root to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

def sync_sources():
    """Synchronize RSS sources with the database - remove unlisted sources and add new ones."""
    user_id = 1  # All sources belong to user ID 1
    
    print("� Starting RSS source synchronization...")
    print(f"📊 Target sources to sync: {len(RSS_SOURCES)}")
    print("-" * 60)
    
    # Import here to avoid circular imports
    from src.services.source_service import get_sources_by_user, delete_source
    
    # Get current sources from database
    current_sources = get_sources_by_user(user_id)
    current_urls = {source.feed_url: source for source in current_sources}
    target_urls = {source['url']: source for source in RSS_SOURCES}
    
    print(f"📋 Current sources in database: {len(current_sources)}")
    print(f"🎯 Target sources in RSS_SOURCES: {len(RSS_SOURCES)}")
    print("-" * 60)
    
    # 1. REMOVE sources not in RSS_SOURCES
    sources_to_remove = []
    for url, source in current_urls.items():
        if url not in target_urls:
            sources_to_remove.append(source)
    
    removed_count = 0
    if sources_to_remove:
        print(f"🗑️  Removing {len(sources_to_remove)} sources not in RSS_SOURCES:")
        for source in sources_to_remove:
            print(f"    Removing: {source.name} ({source.feed_url[:50]}...)")
            if delete_source(source.id, user_id):
                print(f"    ✅ Successfully removed: {source.name}")
                removed_count += 1
            else:
                print(f"    ❌ Failed to remove: {source.name}")
        print()
    
    # 2. ADD new sources from RSS_SOURCES
    added_count = 0
    skipped_count = 0
    
    print(f"➕ Processing {len(RSS_SOURCES)} sources from RSS_SOURCES:")
    for i, source_data in enumerate(RSS_SOURCES, 1):
        print(f"[{i:2d}/{len(RSS_SOURCES)}] Processing: {source_data['name']}")
        
        result = create_source(
            user_id=user_id,
            name=source_data['name'],
            feed_url=source_data['url']
        )
        
        if result:
            print(f"    ✅ Successfully added: {source_data['name']}")
            added_count += 1
        else:
            print(f"    ⏭️  Already exists: {source_data['name']}")
            skipped_count += 1
    
    # Final summary
    print("-" * 60)
    print(f"🎉 Synchronization complete!")
    print(f"🗑️  Removed: {removed_count} outdated sources")
    print(f"✅ Added: {added_count} new sources")
    print(f"⏭️  Unchanged: {skipped_count} existing sources")
    print(f"📊 Total active sources: {len(RSS_SOURCES)}")
    
    if added_count > 0 or removed_count > 0:
        print("\n🔄 Don't forget to run your Lambda ingestion pipeline to fetch articles!")
    
    return added_count, removed_count, skipped_count

if __name__ == "__main__":
    try:
        sync_sources()
    except Exception as e:
        print(f"❌ Error running synchronization: {e}")
        print("Make sure your database is running and accessible.")
        sys.exit(1)
