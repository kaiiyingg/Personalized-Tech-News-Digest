import requests

def is_url_reachable(url, timeout=5):
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        if resp.status_code == 200:
            return True
        # Some sites may not support HEAD, try GET
        resp = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
        return resp.status_code == 200
    except Exception:
        return False
