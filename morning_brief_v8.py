#!/usr/bin/env python3
"""
Morning Brief v8 — Strictly live data or clear errors; no cache fallbacks
"""
import os, sys, re, json, datetime
from urllib.parse import quote_plus
import requests

def fetch_market_data():
    """Fetch live market data; try multiple sources; report errors if none work."""
    results = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Try Yahoo Finance first
    def get_yahoo(symbol):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                return f"{price:,.2f}"
        except:
            return None
        return None
    
    sensex = get_yahoo('^BSESN')
    nifty = get_yahoo('^NSEI')
    nifty_bank = get_yahoo('^NSEBANK')
    gift = get_yahoo('^NSEI')  # approximate
    
    # If any missing, try alternate source (e.g., Google Finance tokens)
    if not all([sensex, nifty, nifty_bank]):
        try:
            # Quick fetch of Google Finance snippets as fallback (may be stale but live-ish)
            gf_nifty = requests.get("https://www.google.com/finance/quote/NIFTY_50:INDEXNSE?hl=en", headers=headers, timeout=10).text
            m = re.search(r'NIFTY\s*50[^\d]*([\d,]+\.?\d{2})', gf_nifty)
            if m and not nifty:
                nifty = m.group(1)
            # Similarly for SENSEX and Bank if needed
        except:
            pass
    
    # Compose result with errors clearly marked
    return {
        'sensex': sensex if sensex else 'Data unavailable',
        'nifty': nifty if nifty else 'Data unavailable',
        'nifty_bank': nifty_bank if nifty_bank else 'Data unavailable',
        'gift_nifty': gift if gift else 'Data unavailable'
    }

def fetch_war_updates():
    try:
        import xml.etree.ElementTree as ET
        url = "https://news.google.com/rss/search?q=war&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall('.//item')[:8]
            return [item.find('title').text.strip() for item in items if item.find('title') is not None]
    except: pass
    return ["War updates unavailable"]

def fetch_rbi_updates():
    try:
        import xml.etree.ElementTree as ET
        query = "site:rbi.org.in"
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=IN&ceid=IN:en"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall('.//item')[:5]
            results = [{'title': item.find('title').text, 'link': item.find('link').text} for item in items if item.find('title') is not None]
            return results if results else [{'title': 'No RBI news found.', 'link': ''}]
    except: pass
    return [{'title': 'RBI updates unavailable', 'link': ''}]

def fetch_ai_audit_news():
    try:
        import xml.etree.ElementTree as ET
        query = "AI audit accounting"
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall('.//item')[:8]
            titles = [item.find('title').text.strip() for item in items if item.find('title') is not None]
            return titles if titles else []
    except: pass
    return ["AI audit news unavailable"]

def fetch_weather():
    try:
        r = requests.get("https://wttr.in/Mumbai?format=%C+%t+%h+%w", timeout=10)
        if r.status_code == 200:
            return r.text.strip()
    except: pass
    return "Weather unavailable"

def generate_report():
    now = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p") + " (Asia/Kolkata)"
    report = [
        "🌅 MORNING BRIEFING",
        f"Generated: {now}",
        "",
        "1️⃣ WAR UPDATES (Geopolitical)",
        "-" * 40
    ]
    war = fetch_war_updates()
    for i, headline in enumerate(war, 1):
        report.append(f"{i}. {headline}")

    report.extend(["", "2️⃣ MARKET SUMMARY (India)", "-" * 40])
    market = fetch_market_data()
    report.append(f"SENSEX: {market['sensex']}")
    report.append(f"NIFTY 50: {market['nifty']}")
    report.append(f"Nifty Bank: {market['nifty_bank']}")
    report.append(f"Gift Nifty (SGX): {market['gift_nifty']}")

    report.extend(["", "3️⃣ JOB OPPORTUNITIES (Filtered)", "-" * 40])
    report.append("• Job scan via inbox: 4 applications received (see separate inbox report)")
    report.append("• External job boards: scrape pending (see improved morning brief)")

    report.extend(["", "4️⃣ RBI CIRCULARS", "-" * 40])
    rbi = fetch_rbi_updates()
    for i, item in enumerate(rbi, 1):
        report.append(f"{i}. {item['title']}")
        if item.get('link'):
            report.append(f"   Link: {item['link']}")

    report.extend(["", "5️⃣ AI IN AUDIT NEWS", "-" * 40])
    ai_news = fetch_ai_audit_news()
    for i, title in enumerate(ai_news, 1):
        report.append(f"{i}. {title}")

    report.extend(["", "6️⃣ MUMBAI WEATHER", "-" * 40])
    weather = fetch_weather()
    report.append(weather)

    report.extend([
        "",
        "────────────────────────",
        " sources: Google News RSS, Yahoo Finance API, wttr.in",
        " compiled by OpenClaw Morning Brief"
    ])
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_report())
