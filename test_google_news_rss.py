#!/usr/bin/env python3
import requests, re

def test_google_news_rss():
    url = "https://news.google.com/rss/search?q=war&hl=en-US&gl=US&ceid=US:en"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    print("Status:", r.status_code)
    # Extract <title> inside <item>
    items = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
    print("Items:", len(items))
    for i, item in enumerate(items[:3]):
        title = re.search(r'<title>([^<]+)</title>', item)
        if title:
            print(f"{i+1}. {title.group(1)}")

test_google_news_rss()
