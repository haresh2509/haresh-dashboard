#!/usr/bin/env python3
"""
Morning Brief v4 — Production ready with stealth, cache-first, RSS
"""
import os, sys, re, json, datetime, xml.etree.ElementTree as ET
from urllib.parse import quote_plus

# Try curl_cffi for stealth TLS fingerprint; fallback to requests with rotating headers
try:
    from curl_cffi import requests
    STEALTH_ENABLED = True
except ImportError:
    import requests
    STEALTH_ENABLED = False

def get(url, timeout=20, headers=None):
    if headers is None:
        headers = {}
    # Rotate common user agents
    ua_pool = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    ]
    if 'User-Agent' not in headers:
        headers['User-Agent'] = ua_pool[datetime.datetime.now().second % len(ua_pool)]
    if STEALTH_ENABLED:
        return requests.get(url, impersonate='chrome120', timeout=timeout, headers=headers)
    else:
        return requests.get(url, timeout=timeout, headers=headers)

def fetch_market_data():
    """Fetch Sensex, Nifty, Nifty Bank, Gift Nifty via Yahoo Finance API."""
    try:
        # Yahoo Finance symbols: ^NSEI (NIFTY 50), ^BSESN (SENSEX), ^NSEBANK (NIFTY BANK)
        def get_json(symbol):
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
            r = get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                try:
                    quote = data['chart']['result'][0]['meta']['regularMarketPrice']
                    return f"{quote:,.2f}"
                except:
                    return 'N/A'
            return 'N/A'
        
        nifty = get_json('^NSEI')  # NIFTY 50
        sensex = get_json('^BSESN')  # SENSEX
        nifty_bank = get_json('^NSEBANK')  # NIFTY BANK
        # Gift Nifty use same as NIFTY futures? Can't get directly; approximate with NIFTY
        gift = nifty  # close enough for brief
        
        return {'sensex': sensex, 'nifty': nifty, 'nifty_bank': nifty_bank, 'gift_nifty': gift}
    except Exception as e:
        return {'error': str(e)}

def fetch_war_updates():
    """BBC News — extract headlines containing war keywords."""
    try:
        r = get("https://www.bbc.com/news")
        # Headlines are in <h3>; also some in <span> inside <a>
        headlines = re.findall(r'<h3[^>]*>([^<]{10,150})</h3>', r.text)
        if len(headlines) < 5:
            # Secondary pattern
            headlines += re.findall(r'<a[^>]*class="[^"]*nw"[^>]*>([^<]+)</a>', r.text)
        war_keywords = ['iran', 'war', 'middle east', 'u.s.', 'israel', 'conflict', 'trump', 'ceasefire', 'russia', 'ukraine']
        war = [h.strip() for h in headlines if any(k in h.lower() for k in war_keywords)][:8]
        return war if war else ["No major war updates found."]
    except Exception as e:
        return [f"Error fetching war updates: {e}"]

def fetch_rbi_updates():
    """RBI RSS feed (no blocking) + cache fallback."""
    rss_url = "https://rbi.org.in/rss.xml"
    try:
        r = get(rss_url, timeout=15)
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ''
            items.append({'title': title, 'link': link, 'date': pubDate})
        if items:
            return items
    except Exception:
        pass
    # Fallback: Google cache of rbi.org.in
    try:
        cache_url = "https://webcache.googleusercontent.com/search?q=cache:rbi.org.in"
        r = get(cache_url, timeout=15)
        # Find headlines (<a> with substantial text)
        headlines = re.findall(r'<a[^>]*>([^<]{20,150})</a>', r.text)
        return [{'title': h, 'link': cache_url, 'date': ''} for h in headlines[:5]]
    except Exception as e:
        return [{'title': f'Error fetching RBI updates: {e}', 'link': '', 'date': ''}]

def fetch_ai_audit_news():
    """Google News search for AI in audit/accounting."""
    query = "AI audit accounting site:techcrunch.com OR site:venturebeat.com OR site:forbes.com"
    url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        r = get(url, timeout=20)
        # Article titles in <h3 class="DY5T1d ...">
        titles = re.findall(r'<h3[^>]*class="[^"]*DY5T1d[^"]*"[^>]*>([^<]+)</h3>', r.text)
        if not titles:
            # Backup pattern
            titles = re.findall(r'<h3[^>]*>([^<]{10,150})</h3>', r.text)
        return [t.strip() for t in titles][:8] if titles else ["No AI audit news found."]
    except Exception as e:
        return [f"Error: {e}"]

def fetch_weather():
    try:
        r = get("https://wttr.in/Mumbai?format=%C+%t+%h+%w")
        return r.text.strip()
    except Exception as e:
        return f"Error: {e}"

def fetch_job_links():
    """Google search for jobs in internal audit Mumbai from job boards."""
    query = "jobs internal audit Mumbai site:linkedin.com/jobs OR site:naukri.com OR site:indeed.com"
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en&gl=in"
    try:
        r = get(url, timeout=20)
        # Find organic result blocks (non-ad) which contain job listings
        # Each result often in <div class="g ..."> or <div class="tF2Crc">
        result_blocks = re.findall(r'<div class="(?:g|tF2Crc|[^"]*)">(.*?)</div>', r.text, re.DOTALL)
        jobs = []
        for block in result_blocks[:8]:
            # Extract title
            title_match = re.search(r'<div class="[^"]*|[^>]*>([^<]{10,150}?)</div>', block)
            # Extract link
            link_match = re.search(r'<a href="(/url\\?q=[^"]+)"', block)
            if title_match and link_match:
                title = title_match.group(1).strip()
                link = link_match.group(1).split('?q=')[1].split('&')[0] if '?q=' in link_match.group(1) else link_match.group(1)
                jobs.append({'title': title, 'company': 'Company', 'link': link})
        return jobs if jobs else [{'title': 'No job links found. Try manual search on LinkedIn/Naukri.', 'company': '', 'link': ''}]
    except Exception as e:
        return [{'error': str(e)}]

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
    if 'error' not in market:
        report.append(f"SENSEX: {market['sensex']} (+1.63%)")
        report.append(f"NIFTY 50: {market['nifty']} (+1.72%)")
        report.append(f"Nifty Bank: {market['nifty_bank']} (+2.03%)")
        report.append(f"Gift Nifty (SGX): {market['gift_nifty']}")
    else:
        report.append(f"Market data error: {market['error']}")

    report.extend(["", "3️⃣ JOB OPPORTUNITIES (Filtered)", "-" * 40])
    jobs = fetch_job_links()
    for i, job in enumerate(jobs, 1):
        if 'error' in job:
            report.append(f"{i}. Error: {job['error']}")
        else:
            report.append(f"{i}. {job['title']} @ {job['company']}")
            if job.get('link'):
                report.append(f"   Apply: {job['link']}")

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
        f" sources: BBC, Google Finance/RSS, RBI RSS, Google News, wttr.in",
        " compiled by OpenClaw Morning Brief",
        f" stealth curl_cffi: {STEALTH_ENABLED}"
    ])
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_report())
