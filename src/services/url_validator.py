"""
URL Validator Service

Provides URL validation and reachability testing functionality:
- HTTP/HTTPS URL reachability verification
- Timeout-based connection testing
- Fallback validation methods for different server configurations
- Used for RSS feed validation during source creation

Optimized for fast validation with reasonable timeout defaults.
"""

import requests

def is_url_reachable(url: str, timeout: int = 5) -> bool:
    """
    Test if a URL is reachable and returns a successful HTTP response.
    
    Uses HEAD request first for efficiency, falls back to GET if needed.
    Some servers don't support HEAD requests properly.
    
    Args:
        url (str): The URL to test for reachability
        timeout (int): Request timeout in seconds (default: 5)
        
    Returns:
        bool: True if URL is reachable with 200 status, False otherwise
    """
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        if resp.status_code == 200:
            return True
        # Some sites may not support HEAD, try GET
        resp = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
        return resp.status_code == 200
    except Exception:
        return False
