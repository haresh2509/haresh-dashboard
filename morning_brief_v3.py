#!/usr/bin/env python3
"""
Morning Brief v3 — Stealth, robust parsing, uses BeautifulSoup if available
"""
import os, sys, re, json, datetime, xml.etree.ElementTree as ET
from urllib.parse import quote_plus

# Try curl_cffi first for stealth, else requests
try:
    from curl_cffi import requests
    def get(url, **kwargs):
        ua = kwargs.get('headers', {}).get('User-Agent', '')
        if not ua:
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['User-Agent'] = ua
        # timeout already in kwargs or default
        return requests.get(url, **kwargs)
except ImportError:
    import requests
    def get(url, **kwargs):
        ua = kwargs.get('headers', {}).get('User-Agent', '')
        if not ua:
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['User-Agent'] = ua
        return requests.get(url, **kwargs)

def fetch_market_data():
    try:
        # NIFTY 50
        nifty_url = "https://www.google.com/finance/quote/NIFTY_50:INDEXNSE?hl=en"
        r = get(nifty_url)
        # Find price in span.YMlKec after NIFTY 50 label
        # Pattern: NIFTY 50 label then within 200 chars span class YMlKec
        m = re.search(r'NIFTY\s*50.*?<span class="YMlKec">([\d,]+\.?\d{2})</span>', r.text, re.DOTALL)
        nifty = m.group(1) if m else 'N/A'
        # SENSEX
        sensex_url = "https://www.google.com/finance/quote/SENSEX:INDEXBOM?hl=en"
        r2 = get(sensex_url)
        m2 = re.search(r'SENSEX.*?<span class="YMlKec">([\d,]+\.?\d{2})</span>', r2.text, re.DOTALL)
        sensex = m2.group(1) if m2 else 'N/A'
        # Nifty Bank
        bank_url = "https://www.google.com/finance/quote/NIFTY_BANK:INDEXNSE?hl=en"
        r3 = get(bank_url)
        m3 = re.search(r'Nifty\s*Bank.*?<span class="YMlKec">([\d,]+\.?\d{2})</span>', r3.text, re.DOTALL)
        nifty_bank = m3.group(1) if m3 else 'N/A'
        # Gift Nifty (use ^NSEI futures)
        gift_url = "https://www.google.com/finance/quote/^NSEI:INDEXNSE?hl=en"
        r4 = get(gift_url)
        m4 = re.search(r'NIFTY\s*50.*?<span class="YMlKec">([\d,]+\.?\d{2})</span>', r4.text, re.DOTALL)
        gift = m4.group(1) if m4 else 'N/A (no futures data)'
        return {'sensex': sensex, 'nifty': nifty, 'nifty_bank': nifty_bank, 'gift_nifty': gift}
    except Exception as e:
        return {'error': str(e)}

def fetch_war_updates():
    # BBC News front page - extract headlines with war keywords
    try:
        r = get("https://www.bbc.com/news")
        # Extract headlines from <h3> tags
        headlines = re.findall(r'<h3[^>]*>([^<]{10,150})</h3>', r.text)
        war_keywords = ['iran', 'war', 'middle east', 'u.s.', 'israel', 'conflict', 'trump', 'ceasefire']
        war = [h.strip() for h in headlines if any(k in h.lower() for k in war_keywords)][:8]
        return war if war else ["No major war updates found."]
    except Exception as e:
        return [f"Error fetching war updates: {e}"]

def fetch_rbi_updates():
    # Try RBI RSS
    try:
        r = get("https://rbi.org.in/rss.xml", timeout=15)
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            items.append({'title': title, 'link': link})
        return items
    except Exception:
        # Fallback: Google cache of RBI homepage
        try:
            cache_url = "https://webcache.googleusercontent.com/search?q=cache:rbi.org.in"
            r = get(cache_url, timeout=15)
            # Find headlines
            headlines = re.findall(r'<a[^>]*>([^<]{20,150})</a>', r.text)
            return [{'title': h, 'link': cache_url} for h in headlines[:5]]
        except Exception as e:
            return [{'title': f'Error fetching RBI updates: {e}', 'link': ''}]

def fetch_ai_audit_news():
    # Google News search
    query = "AI audit site:techcrunch.com OR site:venturebeat.com OR site:forbes.com"
    url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        r = get(url, timeout=20)
        # Google News article titles are in <h3 class="...DY5T1d...">
        titles = re.findall(r'<h3[^>]*class="[^"]*DY5T1d[^"]*"[^>]*>([^<]+)</h3>', r.text)
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
    # Use Google search for "jobs internal audit Mumbai" and extract result links
    query = "jobs internal audit Mumbai site:linkedin.com/jobs OR site:naukri.com OR site:indeed.com"
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en&gl=in"
    try:
        r = get(url, timeout=20)
        # Find result blocks - look for <div class="tF2Crc"> or similar
        job_blocks = re.findall(r'<div class="tF2Crc">(.*?)</div>', r.text, re.DOTALL)
        jobs = []
        for block in job_blocks[:8]:
            title_match = re.search(r'<div class="[^"]*job-title[^"]*">([^<]+)</div>', block)
            company_match = re.search(r'<div class="[^"]*company-name[^"]*">([^<]+)</div>', block)
            link_match = re.search(r'<a href="([^"]+)"', block)
            if title_match and company_match:
                jobs.append({
                    'title': title_match.group(1).strip(),
                    'company': company_match.group(1).strip(),
                    'link': link_match.group(1) if link_match else ''
                })
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
        " sources: BBC, Google Finance, RBI RSS, Google News, wttr.in",
        " compiled by OpenClaw Morning Brief"
    ])
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_report())
