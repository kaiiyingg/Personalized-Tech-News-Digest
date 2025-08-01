"""
Production-ready caching with Redis support and memory fallback
"""
import os
import time
import json
from functools import wraps
from typing import Any, Dict, Optional

# Try to import Redis, fall back to memory cache if not available
try:
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    # Test connection
    redis_client.ping()
    USE_REDIS = True
    print("✅ Redis connected successfully")
except (ImportError, redis.ConnectionError, redis.TimeoutError) as e:
    USE_REDIS = False
    print(f"⚠️  Redis not available, using memory cache: {e}")
    # Fallback to memory cache
    _memory_cache: Dict[str, Dict[str, Any]] = {}

def cache_result(expiry: int = 300):  # 5 minutes default
    """
    Production caching decorator with Redis support
    Falls back to memory cache if Redis is unavailable
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"techdigest:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            if USE_REDIS:
                try:
                    # Try Redis first
                    cached_data = redis_client.get(cache_key)
                    if cached_data:
                        return json.loads(cached_data)
                    
                    # Execute function and cache result
                    result = func(*args, **kwargs)
                    redis_client.setex(cache_key, expiry, json.dumps(result, default=str))
                    return result
                    
                except (redis.ConnectionError, redis.TimeoutError):
                    # Fall back to memory cache if Redis fails
                    return _memory_cache_fallback(func, cache_key, expiry, *args, **kwargs)
            else:
                # Use memory cache
                return _memory_cache_fallback(func, cache_key, expiry, *args, **kwargs)
                
        return wrapper
    return decorator

def _memory_cache_fallback(func, cache_key, expiry, *args, **kwargs):
    """Fallback memory cache implementation"""
    global _memory_cache
    
    # Check if cached result exists and is not expired
    if cache_key in _memory_cache:
        cached_data = _memory_cache[cache_key]
        if time.time() - cached_data['timestamp'] < expiry:
            return cached_data['result']
        else:
            # Remove expired cache
            del _memory_cache[cache_key]
    
    # Execute function and cache result
    result = func(*args, **kwargs)
    _memory_cache[cache_key] = {
        'result': result,
        'timestamp': time.time()
    }
    
    return result

def clear_cache():
    """Clear all cached data"""
    if USE_REDIS:
        try:
            # Clear all techdigest cache keys
            keys = redis_client.keys("techdigest:*")
            if keys:
                redis_client.delete(*keys)
        except (redis.ConnectionError, redis.TimeoutError):
            pass
    else:
        global _memory_cache
        _memory_cache.clear()

def clear_user_cache(user_id: int):
    """Clear cache for specific user"""
    if USE_REDIS:
        try:
            keys = redis_client.keys(f"techdigest:*:{user_id}:*")
            keys.extend(redis_client.keys(f"techdigest:*:{user_id})*"))
            if keys:
                redis_client.delete(*keys)
        except (redis.ConnectionError, redis.TimeoutError):
            pass
    else:
        global _memory_cache
        keys_to_remove = [k for k in _memory_cache.keys() 
                          if f":{user_id}:" in k or f":{user_id})" in k]
        for key in keys_to_remove:
            del _memory_cache[key]

def get_cache_stats():
    """Get cache statistics for monitoring"""
    if USE_REDIS:
        try:
            info = redis_client.info('memory')
            keys_count = len(redis_client.keys("techdigest:*"))
            return {
                'type': 'redis',
                'memory_used': info.get('used_memory_human', 'unknown'),
                'keys_count': keys_count,
                'connected': True
            }
        except (redis.ConnectionError, redis.TimeoutError):
            return {'type': 'redis', 'connected': False}
    else:
        return {
            'type': 'memory',
            'keys_count': len(_memory_cache),
            'connected': True
        }
