#!/usr/bin/env python3
import requests
import time
from urllib.parse import urlparse

# RSS URLs to test (from add_sources.py)
RSS_SOURCES = [
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("Hacker News", "https://hnrss.org/frontpage"),
    ("Wired", "https://www.wired.com/feed/rss"),
    ("TechRadar", "https://www.techradar.com/rss"),
    ("ZDNet", "https://www.zdnet.com/news/rss.xml"),
    ("MIT Technology Review", "https://www.technologyreview.com/feed/"),
    ("Engadget", "https://www.engadget.com/rss.xml"),
    ("9to5Mac", "https://9to5mac.com/feed/"),
    ("Android Police", "https://www.androidpolice.com/feed/"),
    ("Mashable Tech", "https://mashable.com/feeds/rss/all"),
    ("CNET", "https://www.cnet.com/rss/news/"),
    ("IEEE Spectrum", "https://spectrum.ieee.org/rss/fulltext"),
    ("NYT Technology", "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"),
    ("Gizmodo", "https://gizmodo.com/feed"),
    ("CNA Tech News", "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416"),
    ("AI News", "https://www.artificialintelligence-news.com/feed/"),
    ("OpenAI Blog", "https://openai.com/blog/rss.xml"),
    ("KrebsOnSecurity", "https://krebsonsecurity.com/feed/"),
    ("Dark Reading", "https://www.darkreading.com/rss.xml"),
    ("GitHub Blog", "https://github.blog/feed/"),
    ("Stack Overflow Blog", "https://stackoverflow.blog/feed/"),
    ("Dev.to", "https://dev.to/feed"),
    ("Opensource.com", "https://opensource.com/feed"),
    ("KDnuggets", "https://www.kdnuggets.com/feed"),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("EFF Deeplinks", "https://www.eff.org/rss/updates.xml")
]

def test_rss_url(name, url, timeout=8):
    """Test if RSS URL is accessible and contains valid RSS/XML content"""
    try:
        # Try GET request to check both accessibility and content
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            # Check if content looks like RSS/XML
            content_type = response.headers.get('content-type', '').lower()
            text = response.text[:1000].lower()
            
            if ('xml' in content_type or 'rss' in text or '<rss' in text or 
                '<feed' in text or '<?xml' in text):
                return True, f"✅ {name}: Working RSS (Status: {response.status_code})"
            else:
                return False, f"❌ {name}: Not RSS format (Status: {response.status_code})"
        else:
            return False, f"❌ {name}: Status {response.status_code}"
    except requests.exceptions.Timeout:
        return False, f"❌ {name}: Timeout after {timeout}s"
    except requests.exceptions.ConnectionError:
        return False, f"❌ {name}: Connection error"
    except requests.exceptions.RequestException as e:
        return False, f"❌ {name}: Error - {str(e)[:50]}"

def main():
    print("🔍 Testing RSS Feed URLs...")
    print("=" * 70)
    print(f"📊 Total URLs to test: {len(RSS_SOURCES)}")
    print("=" * 70)
    
    working_urls = []
    broken_urls = []
    
    for i, (name, url) in enumerate(RSS_SOURCES, 1):
        print(f"[{i:2d}/{len(RSS_SOURCES)}] Testing {name}... ", end="", flush=True)
        
        is_working, message = test_rss_url(name, url)
        # Extract just the status part for cleaner output
        status = message.split(': ', 1)[1] if ': ' in message else message
        print(status)
        
        if is_working:
            working_urls.append((name, url))
        else:
            broken_urls.append((name, url, message))
        
        # Shorter delay since we have more URLs to test
        time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print(f"✅ Working RSS feeds: {len(working_urls)}/{len(RSS_SOURCES)} ({len(working_urls)/len(RSS_SOURCES)*100:.1f}%)")
    print(f"❌ Broken RSS feeds: {len(broken_urls)}/{len(RSS_SOURCES)} ({len(broken_urls)/len(RSS_SOURCES)*100:.1f}%)")
    
    if broken_urls:
        print(f"\n🚫 BROKEN RSS FEEDS ({len(broken_urls)} total):")
        print("-" * 50)
        for i, (name, url, error) in enumerate(broken_urls, 1):
            status = error.split(': ', 1)[1] if ': ' in error else error
            print(f"{i:2d}. {name}")
            print(f"    URL: {url}")
            print(f"    Issue: {status}")
            print()
    
    if working_urls:
        print(f"✅ Successfully validated {len(working_urls)} working RSS feeds!")
        
        # Show categories of working feeds
        security_feeds = [name for name, url in working_urls if any(term in name.lower() for term in ['security', 'hack', 'threat', 'krebs', 'dark', 'bleeping'])]
        ai_feeds = [name for name, url in working_urls if any(term in name.lower() for term in ['ai', 'data science', 'openai', 'google ai'])]
        dev_feeds = [name for name, url in working_urls if any(term in name.lower() for term in ['github', 'stack', 'dev.to', 'opensource'])]
        
        if security_feeds:
            print(f"\n🔒 Security feeds ({len(security_feeds)}): {', '.join(security_feeds[:3])}{'...' if len(security_feeds) > 3 else ''}")
        if ai_feeds:
            print(f"🤖 AI/ML feeds ({len(ai_feeds)}): {', '.join(ai_feeds[:3])}{'...' if len(ai_feeds) > 3 else ''}")
        if dev_feeds:
            print(f"💻 Developer feeds ({len(dev_feeds)}): {', '.join(dev_feeds[:3])}{'...' if len(dev_feeds) > 3 else ''}")
    
    return working_urls, broken_urls

if __name__ == "__main__":
    working, broken = main()
