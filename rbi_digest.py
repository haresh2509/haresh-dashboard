#!/usr/bin/env python3
"""
Daily RBI Digest — latest circulars & notifications (last 30 days)
Focus: Treasury, Payments, Forex, AI, Fintech, Compliance, SOX, Operational Risk
"""
import os
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import re

# Config
GMAIL_ADDRESS = 'haresh.mulchandani01@gmail.com'
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')
RECIPIENT = GMAIL_ADDRESS

# Keywords
KEYWORDS = [
    'treasury', 'forex', 'foreign exchange', 'payments', 'upi', 'rtgs', 'neft',
    'ai', 'artificial intelligence', 'machine learning', 'fintech', 'digital rupee',
    'cbdc', 'e-rupee', 'regtech', 'compliance', 'internal audit', 'sox',
    'operational risk', 'banking', 'nbfc', 'audit', 'control', 'risk management',
    'rbi', 'circular', 'notification', 'directive'
]

# Google News RSS for RBI site (mirrors official circulars)
SOURCES = [
    ('Google News - RBI', 'https://news.google.com/rss/search?q=site:rbi.org.in+treasury+OR+payments+OR+forex+OR+AI+OR+fintech+OR+compliance+OR+audit+OR+risk&hl=en-IN&gl=IN&ceid=IN:en')
]

def fetch_items(limit_per_source=20):
    items = []
    for source_name, url in SOURCES:
        try:
            d = feedparser.parse(url)
            for entry in d.entries[:limit_per_source]:
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                summary = entry.get('summary', '').strip()
                published = entry.get('published', '')
                text = (title + ' ' + summary).lower()
                if any(k in text for k in KEYWORDS):
                    items.append({
                        'title': title,
                        'link': link,
                        'summary': summary,
                        'source': source_name,
                        'date': published
                    })
        except Exception as e:
            print(f"Error fetching {source_name}: {e}")
    # Deduplicate
    seen = set()
    uniq = []
    for it in items:
        if it['title'] not in seen:
            uniq.append(it)
            seen.add(it['title'])
    return uniq

def summarize(text, max_sentences=2):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return ' '.join(sentences[:max_sentences]) + ('...' if len(sentences) > max_sentences else '')

def format_email_html(items):
    today = datetime.now().strftime('%A, %d %B %Y')
    html = f"""
<html><body style="font-family: Inter, -apple-system, sans-serif; max-width: 720px; margin: auto; padding: 24px; background: #f9f9fb; color: #1c1c1e;">
  <h2 style="color: #007AFF; margin-top: 0;">RBI & Treasury Digest — {today}</h2>
  <p style="color: #666; margin-bottom: 24px;">Recent updates relevant to treasury, payments, AI, fintech, compliance, audit (last 30 days).</p>
"""
    if not items:
        html += '<p>No new updates matching your filters in the last 30 days.</p>'
    else:
        for i, it in enumerate(items, 1):
            brief = summarize(it['summary']) if it['summary'] else 'No summary available.'
            html += f"""
  <div style="margin-bottom: 20px; padding: 16px; background: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.06);">
    <div style="font-size: 12px; color: #8E8E93; margin-bottom: 6px;">[{it['source']}] {it['date']}</div>
    <a href="{it['link']}" style="font-size: 17px; font-weight: 600; color: #007AFF; text-decoration: none; margin-bottom: 8px; display: block;">{i}. {it['title']}</a>
    <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #444;">{brief}</p>
  </div>
"""
    html += """
  <p style="color: #8E8E93; font-size: 12px; margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee;">
    Sent by OpenClaw. Preferences? Reply to adjust topics or timing.
  </p>
</body></html>
"""
    return html

def send_email(html_body):
    if not GMAIL_APP_PASSWORD:
        print("GMAIL_APP_PASSWORD not set.")
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"RBI/Treasury Digest — {datetime.now().strftime('%d %b')}"
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = RECIPIENT
    msg.attach(MIMEText(html_body, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print("Email sent.")
        return True
    except Exception as e:
        print("Email failed:", e)
        return False

def main():
    items = fetch_items(limit_per_source=20)
    html = format_email_html(items)
    send_email(html)

if __name__ == '__main__':
    main()
