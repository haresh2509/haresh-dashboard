#!/usr/bin/env python3
import re, json

with open('/tmp/google_sensex.html') as f:
    sensex_html = f.read()
with open('/tmp/google_nifty.html') as f:
    nifty_html = f.read()

# Try to find the numeric values in a more robust way
def extract_price(html, label):
    # Look for the label followed by a number with comma
    pat = rf'{label}[^0-9]*([\d,]+\.?\d{{0,2}})'
    m = re.search(pat, html, re.IGNORECASE)
    if m:
        return m.group(1)
    return None

sensex_val = extract_price(sensex_html, 'SENSEX')
nifty_val = extract_price(nifty_html, 'NIFTY 50')

print(f"SENSEX: {sensex_val}")
print(f"NIFTY: {nifty_val}")

# Also try to get percent changes
pct_pat = r'([+\-]?\d+\.\d+%)'
sensex_pcts = re.findall(pct_pat, sensex_html)
nifty_pcts = re.findall(pct_pat, nifty_html)
print("SENSEX pcts:", sensex_pcts[:3])
print("NIFTY pcts:", nifty_pcts[:3])
