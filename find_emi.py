#!/usr/bin/env python3
"""Find EMI-like transactions in Axis Bank emails from March."""
import os, re, datetime, imaplib, email
from email.header import decode_header

env_path = '/home/haresh/.openclaw/workspace/.env.gmail'
env = {}
with open(env_path) as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v.strip()

imap = imaplib.IMAP4_SSL("imap.gmail.com")
imap.login(env['GMAIL_ADDRESS'], env['GMAIL_APP_PASSWORD'])
imap.select("INBOX")

# Search Axis emails in March
since = "01-Mar-2025" if datetime.datetime.now().year == 2025 else "01-Mar-2026"
status, data = imap.search(None, f'(SINCE "{since}" FROM "axis.bank.in")')
eids = data[0].split()

emi_candidates = []
for eid in eids:
    status, msg_data = imap.fetch(eid, '(RFC822)')
    if status != 'OK':
        continue
    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw)
    subject = decode_header(msg.get('Subject', ''))[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode(errors='ignore')
    # Get body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except:
                    pass
        if not body:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    try:
                        html = part.get_payload(decode=True).decode()
                        body = re.sub(r'<[^>]+>', ' ', html)
                        break
                    except:
                        pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            pass
    if not body:
        continue
    # Look for EMI or Loan Payment Credit
    if re.search(r'EMI|loan.*payment|payment.*credit.*loan', body, re.IGNORECASE):
        # Extract amount and date
        amt = re.search(r'(?:Rs\.?|₹|INR)\s*([\d,]+\.?\d{2})', body)
        date = re.search(r'Date\s*&\s*Time:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', body, re.IGNORECASE)
        emi_candidates.append({
            'subject': subject,
            'date': date.group(1) if date else 'N/A',
            'amount': amt.group(1) if amt else 'N/A',
            'snippet': body[:200]
        })

imap.logout()

print(f"Found {len(emi_candidates)} EMI-like messages in March")
for e in emi_candidates[-10:]:  # show recent ones
    print(f"{e['date']} | {e['amount']} | {e['subject'][:60]}")
