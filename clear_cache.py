#!/usr/bin/env python3
"""Clear Redis cache for immediate refresh"""

import redis
import os

def clear_cache():
    """Clear Redis cache to force fresh content loading"""
    try:
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        
        # Clear all cache keys
        cache_keys = r.keys('*')
        if cache_keys:
            r.delete(*cache_keys)
            print(f"Cleared {len(cache_keys)} cache entries")
        else:
            print("No cache entries found")
            
        print("Cache cleared successfully!")
        
    except Exception as e:
        print(f"Error clearing cache: {e}")
        print("Cache may not be available or configured")

if __name__ == "__main__":
    clear_cache()
