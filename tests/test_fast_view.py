import sys
sys.path.append('/app/src')
from services.content_service import get_articles_by_topics
from services.user_service import get_user_topics

# Test with a sample user ID (1)
user_id = 1
print('Testing Fast View logic...')

# Check user topics
user_topics = get_user_topics(user_id)
print(f'User {user_id} topics: {user_topics}')

# Test the Fast View function
result = get_articles_by_topics(user_id, limit_per_topic=10)
fast_view_articles = result.get('fast_view', [])

print(f'Fast view articles count: {len(fast_view_articles)}')
if fast_view_articles:
    for i, article in enumerate(fast_view_articles[:3]):
        if isinstance(article, dict) and article.get('id'):
            print(f'  {i+1}. {article.get("title", "No title")[:50]}... (Topic: {article.get("topic", "Unknown")})')
else:
    print('No fast view articles found')
