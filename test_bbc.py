#!/usr/bin/env python3
import requests, re

def test_bbc():
    url = "https://www.bbc.com/news"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    print("BBC status:", r.status_code)
    headlines = re.findall(r'<h3[^>]*>([^<]{10,150})</h3>', r.text)
    print("Headlines found:", len(headlines))
    war_keywords = ['iran', 'war', 'middle east', 'u.s.', 'israel', 'conflict', 'trump', 'ceasefire', 'russia', 'ukraine']
    war = [h.strip() for h in headlines if any(k in h.lower() for k in war_keywords)][:8]
    print("War-related:", len(war))
    for w in war:
        print("-", w)

test_bbc()
