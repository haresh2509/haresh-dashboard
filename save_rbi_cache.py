#!/usr/bin/env python3
import requests

cache_url = "https://webcache.googleusercontent.com/search?q=cache:rbi.org.in"
r = requests.get(cache_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
with open('/tmp/rbi_cache.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
print("Saved, length:", len(r.text))
