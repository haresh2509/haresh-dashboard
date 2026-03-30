#!/usr/bin/env python3
import re, requests, datetime

def get(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    return requests.get(url, headers=headers, timeout=20)

def fetch_market():
    try:
        # NIFTY 50
        r = get("https://www.google.com/finance/quote/NIFTY_50:INDEXNSE?hl=en")
        # Find any large number (>=1000) that appears after NIFTY 50
        m = re.search(r'NIFTY\s*50[^\d]*(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)', r.text)
        nifty = m.group(1) if m else 'N/A'
        # SENSEX
        r2 = get("https://www.google.com/finance/quote/SENSEX:INDEXBOM?hl=en")
        m2 = re.search(r'SENSEX[^\d]*(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)', r2.text)
        sensex = m2.group(1) if m2 else 'N/A'
        # Nifty Bank
        r3 = get("https://www.google.com/finance/quote/NIFTY_BANK:INDEXNSE?hl=en")
        m3 = re.search(r'Nifty\s*Bank[^\d]*(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)', r3.text)
        nifty_bank = m3.group(1) if m3 else 'N/A'
        return sensex, nifty, nifty_bank
    except Exception as e:
        return 'N/A', 'N/A', f'Error: {e}'

sensex, nifty, bank = fetch_market()
print(f"SENSEX: {sensex}")
print(f"NIFTY: {nifty}")
print(f"Bank: {bank}")
