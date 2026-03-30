#!/usr/bin/env python3
import re, requests

def get(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    return requests.get(url, headers=headers, timeout=15)

def test_market():
    def get_price(html, label):
        patterns = [
            rf'{label}.*?<span[^>]*>([\d,]+\.?\d{{0,2}})</span>',
            rf'{label}[^\d]*(\d{{1,3}}(?:,\d{{3}})+(?:\.\d{{0,2}})?)'
        ]
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
            if m:
                return m.group(1)
        return 'N/A'

    urls = {
        'NIFTY 50': "https://www.google.com/finance/quote/NIFTY_50:INDEXNSE?hl=en",
        'SENSEX': "https://www.google.com/finance/quote/SENSEX:INDEXBOM?hl=en",
        'Nifty Bank': "https://www.google.com/finance/quote/NIFTY_BANK:INDEXNSE?hl=en"
    }
    for name, url in urls.items():
        r = get(url)
        price = get_price(r.text, name)
        print(f"{name} -> {price} (URL status: {r.status_code})")

test_market()
