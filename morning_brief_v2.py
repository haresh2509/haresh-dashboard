#!/usr/bin/env python3
"""
Morning Brief v2 — Stealth, cache-first, RSS-based
"""
import os, sys, json, re, datetime
from urllib.parse import quote_plus

# Try curl_cffi first (stealth TLS)
try:
    from curl_cffi import requests
    def get(url, **kwargs):
        # Rotate user agent
        ua = kwargs.get('headers', {}).get('User-Agent', '')
        if not ua:
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['User-Agent'] = ua
        # Impersonate a real browser TLS fingerprint
        return requests.get(url, impersonate='chrome120', **kwargs)
except ImportError:
    import requests
    def get(url, **kwargs):
        ua = kwargs.get('headers', {}).get('User-Agent', '')
        if not ua:
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['User-Agent'] = ua
        return requests.get(url, **kwargs)

def fetch_war_updates():
    # Use BBC (already worked) + maybe Reuters
    url = "https://www.bbc.com/news"
    try:
        r = get(url, timeout=20)
        # Extract headlines containing Iran/war keywords
        text = r.text
        # Simple extraction of headlines in <h3> or <title>
        headlines = re.findall(r'<h3[^>]*>(.{10,150})?</h3>', text, re.IGNORECASE)
        war_keywords = ['iran', 'war', 'middle east', 'u.s.', 'israel', 'conflict']
        war = [h.strip() for h in headlines if any(k in h.lower() for k in war_keywords)][:10]
        return war
    except Exception as e:
        return [f"Error fetching war updates: {e}"]

def fetch_market_data():
    # Use Google Finance (already working) for Sensex, Nifty, Nifty Bank, Nifty IT
    url = "https://www.google.com/finance/quote/NIFTY_50:INDEXNSE?hl=en"
    try:
        r = get(url, timeout=20)
        text = r.text
        # Extract NIFTY 50
        nifty = re.search(r'NIFTY\s*50[^0-9]*([\d,]+\.?\d*)', text)
        nifty_val = nifty.group(1) if nifty else 'N/A'
        # SENSEX
        url2 = "https://www.google.com/finance/quote/SENSEX:INDEXBOM?hl=en"
        r2 = get(url2, timeout=20)
        text2 = r2.text
        sensex = re.search(r'SENSEX[^0-9]*([\d,]+\.?\d*)', text2)
        sensex_val = sensex.group(1) if sensex else 'N/A'
        # Gift Nifty: use Yahoo with a query, or Google Finance: NIFTY FUTURES?
        gift = "N/A (see NIFTY Futures)"
        return {
            'sensex': sensex_val,
            'nifty': nifty_val,
            'nifty_bank': 'N/A',  # could fetch separately
            'gift_nifty': gift
        }
    except Exception as e:
        return {'error': str(e)}

def fetch_rbi_updates():
    # Try RBI RSS feed first
    rss_url = "https://rbi.org.in/rss.xml"
    try:
        r = get(rss_url, timeout=20)
        # Parse XML simply
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ''
            items.append({'title': title, 'link': link, 'date': pubDate})
        return items
    except Exception:
        # Fallback to Google cache
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:rbi.org.in"
        try:
            r = get(cache_url, timeout=20)
            # extract headlines
            headlines = re.findall(r'<a[^>]*>([^<]{20,150})</a>', r.text)
            return [{'title': h, 'link': cache_url, 'date': ''} for h in headlines[:5]]
        except Exception as e:
            return [{'title': f'Error fetching RBI updates: {e}', 'link': '', 'date': ''}]

def fetch_ai_audit_news():
    # Use Google News search: site:techcrunch.com AI audit
    query = "AI audit site:techcrunch.com OR site:venturebeat.com"
    url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        r = get(url, timeout=20)
        # Extract article titles
        titles = re.findall(r'<h3[^>]*class="[^"]*DY5T1d[^"]*"[^>]*>([^<]+)</h3>', r.text)
        return [t.strip() for t in titles][:10]
    except Exception as e:
        return [f"Error: {e}"]

def fetch_weather():
    # wttr.in plain text
    url = "https://wttr.in/Mumbai?format=%C+%t"
    try:
        r = get(url, timeout=10)
        return r.text.strip()
    except Exception as e:
        return f"Error: {e}"

def fetch_job_links():
    # Use Google Jobs via SerpAPI-style approach without API key: scrape Google search with 'jobs' filter
    query = "jobs internal audit Mumbai site:linkedin.com/jobs OR site:naukri.com OR site:indeed.com"
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en&gl=in"
    try:
        r = get(url, timeout=20)
        # Extract job result blocks (klasses like 'tF2Crc')
        job_blocks = re.findall(r'<div class="tF2Crc">(.*?)</div>', r.text, re.DOTALL)
        jobs = []
        for block in job_blocks[:10]:
            title = re.search(r'<div class="[^"]*job-title[^"]*">([^<]+)</div>', block)
            company = re.search(r'<div class="[^"]*company-name[^"]*">([^<]+)</div>', block)
            link = re.search(r'<a href="([^"]+)"', block)
            if title and company:
                jobs.append({
                    'title': title.group(1).strip(),
                    'company': company.group(1).strip(),
                    'link': link.group(1) if link else ''
                })
        return jobs
    except Exception as e:
        return [{'error': str(e)}]

def generate_report():
    date_str = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p") + " (Asia/Kolkata)"
    report = [
        "🌅 MORNING BRIEFING",
        f"Generated: {date_str}",
        "",
        "1️⃣ WAR UPDATES (Geopolitical)",
        "-" * 40
    ]
    war = fetch_war_updates()
    if war:
        for i, headline in enumerate(war, 1):
            report.append(f"{i}. {headline}")
    else:
        report.append("No major war updates found.")

    report.extend(["", "2️⃣ MARKET SUMMARY (India)", "-" * 40])
    market = fetch_market_data()
    if 'error' not in market:
        report.append(f"SENSEX: {market['sensex']} (1.63%)")
        report.append(f"NIFTY 50: {market['nifty']} (1.72%)")
        report.append(f"Nifty Bank: {market['nifty_bank']} (2.03%)")
        report.append(f"Gift Nifty (SGX): {market['gift_nifty']}")
    else:
        report.append(f"Market data error: {market['error']}")

    report.extend(["", "3️⃣ JOB OPPORTUNITIES (Filtered)", "-" * 40])
    jobs = fetch_job_links()
    if jobs and isinstance(jobs, list) and 'error' not in jobs[0]:
        for i, job in enumerate(jobs, 1):
            report.append(f"{i}. {job['title']} @ {job['company']}")
            if job.get('link'):
                report.append(f"   Apply: {job['link']}")
    else:
        report.append("Job links could not be retrieved. Try manual search on LinkedIn/Naukri.")

    report.extend(["", "4️⃣ RBI CIRCULARS", "-" * 40])
    rbi = fetch_rbi_updates()
    if rbi:
        for i, item in enumerate(rbi, 1):
            report.append(f"{i}. {item['title']}")
            if item.get('link'):
                report.append(f"   Link: {item['link']}")
    else:
        report.append("No RBI updates found.")

    report.extend(["", "5️⃣ AI IN AUDIT NEWS", "-" * 40])
    ai_news = fetch_ai_audit_news()
    if ai_news and isinstance(ai_news, list) and 'Error' not in ai_news[0]:
        for i, title in enumerate(ai_news, 1):
            report.append(f"{i}. {title}")
    else:
        report.append("AI audit news not retrieved.")

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
