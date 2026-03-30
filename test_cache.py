#!/usr/bin/env python3
import requests, re

def test_google_cache():
    cache_url = "https://webcache.googleusercontent.com/search?q=cache:rbi.org.in"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(cache_url, headers=headers, timeout=15)
    print("Cache status:", r.status_code)
    if r.status_code == 200:
        # Find headlines
        headlines = re.findall(r'<a[^>]*>([^<]{20,150})</a>', r.text)
        print("Found headlines:", len(headlines))
        for h in headlines[:5]:
            print("-", h)

test_google_cache()
