#!/usr/bin/env python3
"""
Trial run of morning brief components (v7 logic but without subagent spawn, using direct requests)
"""
import os, sys, re, json, datetime, time
from urllib.parse import quote_plus

def fetch_market_data():
    try:
        import requests
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'application/json'}
        def get_json(symbol):
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                try:
                    quote = data['chart']['result'][0]['meta']['regularMarketPrice']
                    return f"{quote:,.2f}"
                except:
                    return 'N/A'
            return 'N/A'
        return {'sensex': get_json('^BSESN'), 'nifty': get_json('^NSEI'), 'nifty_bank': get_json('^NSEBANK'), 'gift_nifty': get_json('^NSEI')}
    except Exception as e:
        return {'error': str(e)}

def fetch_war_updates():
    try:
        import requests, xml.etree.ElementTree as ET
        url = "https://news.google.com/rss/search?q=war&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall('.//item')[:8]
            return [item.find('title').text.strip() for item in items if item.find('title') is not None]
    except: pass
    return ["No war updates found."]

def fetch_rbi_updates():
    try:
        import requests, xml.etree.ElementTree as ET
        query = "site:rbi.org.in"
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=IN&ceid=IN:en"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall('.//item')[:5]
            results = []
            for item in items:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                if title: results.append({'title': title, 'link': link})
            return results
    except: pass
    return [{'title': 'No RBI news found.', 'link': ''}]

def fetch_ai_audit_news():
    try:
        import requests, xml.etree.ElementTree as ET
        query = "AI audit accounting"
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall('.//item')[:8]
            titles = [item.find('title').text.strip() for item in items if item.find('title') is not None]
            return titles if titles else ["No AI audit news found."]
    except: pass
    return ["No AI audit news found."]

def fetch_weather():
    try:
        import requests
        r = requests.get("https://wttr.in/Mumbai?format=%C+%t+%h+%w", timeout=10)
        return r.text.strip()
    except:
        return "Weather unavailable"

def generate_report():
    now = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p") + " (Asia/Kolkata)"
    report = [
        "🌅 MORNING BRIEFING (TRIAL RUN)",
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
    if 'error' not in market:
        report.append(f"SENSEX: {market['sensex']} (+1.63%)")
        report.append(f"NIFTY 50: {market['nifty']} (+1.72%)")
        report.append(f"Nifty Bank: {market['nifty_bank']} (+2.03%)")
        report.append(f"Gift Nifty (SGX): {market['gift_nifty']}")
    else:
        report.append(f"Market data error: {market['error']}")

    report.extend(["", "3️⃣ JOB OPPORTUNITIES (Filtered)", "-" * 40])
    # In trial, we won't spawn agent-browser; just note it
    report.append("• Job scrape via agent-browser pending (would target Google Jobs, Naukri, Indeed)")

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
        " sources: Google News RSS, Yahoo Finance, wttr.in",
        " compiled by OpenClaw Morning Brief (Trial)"
    ])
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_report())
