#!/usr/bin/env python3
import re, requests, datetime, xml.etree.ElementTree as ET
from urllib.parse import quote_plus

def get(url, **kwargs):
    ua = kwargs.get('headers', {}).get('User-Agent', '')
    if not ua:
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    kwargs['headers'] = kwargs.get('headers', {})
    kwargs['headers']['User-Agent'] = ua
    return requests.get(url, timeout=15, **kwargs)

def fetch_market_debug():
    url = "https://www.google.com/finance/quote/NIFTY_50:INDEXNSE?hl=en"
    r = get(url)
    print("NIFTY response length:", len(r.text))
    m = re.search(r'NIFTY\s*50[^0-9]*([\d,]+\.?\d*)', r.text)
    print("NIFTY match:", m.group(1) if m else "None")
    url2 = "https://www.google.com/finance/quote/SENSEX:INDEXBOM?hl=en"
    r2 = get(url2)
    print("SENSEX response length:", len(r2.text))
    m2 = re.search(r'SENSEX[^0-9]*([\d,]+\.?\d*)', r2.text)
    print("SENSEX match:", m2.group(1) if m2 else "None")
    # Save for inspection
    with open('/tmp/google_nifty.html', 'w') as f: f.write(r.text)
    with open('/tmp/google_sensex.html', 'w') as f: f.write(r2.text)
    print("Saved HTML to /tmp for inspection")

fetch_market_debug()
