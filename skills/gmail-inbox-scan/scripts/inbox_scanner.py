#!/usr/bin/env python3
"""
Gmail Inbox Scanner — job & urgent email detection with draft replies.
"""
import imaplib
import email
from email.header import decode_header
import os
import re
from datetime import datetime, timedelta
import sys

# Load credentials from .env.gmail (workspace root)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '.env.gmail')
env_path = os.path.normpath(env_path)
credentials = {}
try:
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                credentials[k] = v
except Exception as e:
    print(f"Error reading .env.gmail: {e}", file=sys.stderr)
    sys.exit(1)

GMAIL_ADDRESS = credentials.get('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = credentials.get('GMAIL_APP_PASSWORD')

if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
    print("Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD in .env.gmail", file=sys.stderr)
    sys.exit(1)

# Classification keywords
job_keywords = ['application', 'job', 'position', 'resume', 'cv', 'recruitment', 'hiring', 'interview', 'vacancy', 'role']
urgent_keywords = ['urgent', 'asap', 'immediate', 'deadline', 'action required', 'important', 'priority', 'time sensitive', 'expire', 'last chance', 'respond by']
promotional_indicators = ['unsubscribe', 'newsletter', 'promotion', 'sale', 'discount', 'offer', 'deal', 'price', 'advertisement', 'marketing', 'click here', 'buy now']
job_domains = ['linkedin.com', 'naukri.com', 'indeed.com', 'glassdoor.com', 'monster.com', 'shine.com', 'timesjobs.com', 'foundit.in', 'iimjobs.com', 'hiremee', 'hired', 'ziprecruiter', 'myworkday.com', 'oraclecloud.com']

# Senders to exclude from job classification (specific non-job senders)
exclude_senders = [
    'axis.bank.in', 'axisbankmail.bank.in', 'digital.axisbankmail',
    'citibank', 'citi', 'hdfc', 'sbi', 'icici', 'kotak', 'rbl', 'idfc'
]

def decode_mime_header(s):
    if s is None:
        return ""
    decoded = decode_header(s)
    parts = []
    for part, enc in decoded:
        if isinstance(part, bytes):
            try:
                parts.append(part.decode(enc if enc else 'utf-8', errors='ignore'))
            except:
                parts.append(part.decode('utf-8', errors='ignore'))
        else:
            parts.append(part)
    return ''.join(parts)

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_dispo = str(part.get('Content-Disposition') or '')
            if content_type == 'text/plain' and 'attachment' not in content_dispo:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(errors='ignore')
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(errors='ignore')
        except:
            pass
    return ""

def clean_text(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_name_email(from_header):
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        email_addr = match.group(1)
        name = from_header.split('<')[0].strip().replace('"', '').replace("'", "")
        if name == email_addr:
            name = ""
        return name, email_addr
    else:
        if '@' in from_header:
            return "", from_header
        else:
            return from_header, ""

def classify_email(subject, body, from_addr):
    subject_lower = subject.lower()
    body_lower = body.lower() if body else ""
    from_lower = from_addr.lower()

    # Exclude known non-job senders outright unless from a job platform
    is_excluded_sender = any(excl in from_lower for excl in exclude_senders)
    is_job_site = any(domain in from_lower for domain in job_domains)
    if is_excluded_sender and not is_job_site:
        is_promo = any(ind in body_lower or ind in subject_lower for ind in promotional_indicators)
        is_urgent = any(kw in subject_lower or kw in body_lower for kw in urgent_keywords)
        actionable = is_urgent and not is_promo
        if actionable:
            return actionable, "High", "Urgent", is_promo
        else:
            return False, "Low", "Official", is_promo

    promo_count = sum(1 for ind in promotional_indicators if ind in body_lower or ind in subject_lower)
    is_promo = promo_count >= 2

    is_job = any(kw in subject_lower or kw in body_lower for kw in job_keywords)
    if is_job_site:
        is_job = True

    is_urgent = any(kw in subject_lower or kw in body_lower for kw in urgent_keywords)

    actionable = (is_job and not is_promo) or (is_urgent and not is_promo)

    if actionable:
        if is_job:
            category = "Job"
            urgency = "High" if is_urgent and not is_promo else "Medium"
        else:
            category = "Urgent"
            urgency = "High"
    else:
        category = "Official"
        urgency = "Low"

    return actionable, urgency, category, is_promo

def generate_draft_reply(name, category, subject, is_promo):
    if is_promo:
        return None
    if category != "Job":
        return None
    greeting = f"Dear {name}," if name else "Dear Hiring Manager,"
    return f"""{greeting}

Thank you for your email regarding "{subject}". I am very interested in this opportunity and believe my experience aligns well with the requirements. I have attached my resume for your review and welcome the chance to discuss further.

Best regards,
Haresh Mulchandani, CA
📞 +91 7021544904
📧 haresh.mulchandani01@gmail.com
🔗 linkedin.com/in/haresh4744"""

if __name__ == "__main__":
    # Connect to Gmail IMAP
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    except Exception as e:
        print(f"IMAP connection/login failed: {e}", file=sys.stderr)
        sys.exit(1)

    imap.select("INBOX")
    since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
    status, messages = imap.search(None, f'(SINCE "{since_date}")')
    if status != 'OK':
        print("Search failed", file=sys.stderr)
        imap.logout()
        sys.exit(1)

    email_ids = messages[0].split()
    email_ids = email_ids[-50:]  # limit

    actionable_emails = []

    for eid in email_ids:
        try:
            status, data = imap.fetch(eid, '(RFC822)')
            if status != 'OK' or not data or not data[0]:
                continue
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = decode_mime_header(msg['Subject'])
            from_header = decode_mime_header(msg['From'])
            name, email_addr = extract_name_email(from_header)
            if not email_addr:
                email_addr = from_header
            date_str = msg['Date'] or ""
            body = get_body(msg)
            body_clean = clean_text(body)

            actionable, urgency, category, is_promo = classify_email(subject, body_clean, email_addr)

            if actionable:
                draft = generate_draft_reply(name, category, subject, is_promo)
                actionable_emails.append({
                    'sender': from_header,
                    'email_addr': email_addr,
                    'name': name,
                    'subject': subject,
                    'date': date_str,
                    'urgency': urgency,
                    'category': category,
                    'is_promo': is_promo,
                    'draft': draft
                })
        except Exception:
            pass

    imap.close()
    imap.logout()

    # Generate report
    timezone = "Asia/Kolkata"
    now = datetime.now().astimezone().strftime("%A, %d %B %Y, %I:%M %p") + f" ({timezone})"
    since = (datetime.now() - timedelta(days=1)).strftime("%d %b %Y")
    total_scanned = len(email_ids)
    actionable_count = len(actionable_emails)

    report_lines = [
        "GMAIL INBOX SCAN REPORT",
        f"Generated: {now}",
        f"Period scanned: Last 1 day (since {since})",
        f"Total emails found: {total_scanned}",
        f"Actionable items (High Urgency / Job-Related): {actionable_count}",
        "",
        "--- PRIORITY ITEMS ---",
        ""
    ]

    if actionable_count == 0:
        report_lines.append("No actionable emails found in the scan period.")
    else:
        for idx, item in enumerate(actionable_emails, 1):
            if item['category'] == 'Job':
                emoji = "🚨💼" if item['urgency'] == 'High' else "💼"
            elif item['urgency'] == 'High':
                emoji = "🚨"
            else:
                emoji = "📬"
            report_lines.append(f"{idx}. {emoji} {item['sender']}")
            report_lines.append(f"   Subject: {item['subject']}")
            report_lines.append(f"   Date: {item['date']}")
            report_lines.append(f"   Urgency: {item['urgency']} | Category: {item['category']}")
            if item['category'] == 'Job':
                report_lines.append("   Suggested Actions: Review application status, Send acknowledgment/thank you")
            else:
                report_lines.append("   Suggested Actions: Respond promptly")
            if item['is_promo']:
                report_lines.append("   ⚠️ Note: This appears to be a promotional email. No reply needed. Consider unsubscribing or marking as spam.")
            draft = item.get('draft')
            if draft:
                report_lines.append("   📝 DRAFT REPLY (for approval):")
                report_lines.append("   ```")
                for line in draft.split('\n'):
                    report_lines.append(f"   {line}")
                report_lines.append("   ```")
            report_lines.append("")

    print("\n".join(report_lines))
