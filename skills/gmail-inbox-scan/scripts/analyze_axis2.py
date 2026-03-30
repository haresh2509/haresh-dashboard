#!/usr/bin/env python3
import os, imaplib, email, re, html
from email.header import decode_header

env_path = '/home/haresh/.openclaw/workspace/.env.gmail'
env = {}
with open(env_path) as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v.strip()

imap = imaplib.IMAP4_SSL('imap.gmail.com')
imap.login(env['GMAIL_ADDRESS'], env['GMAIL_APP_PASSWORD'])
imap.select('INBOX')

data = imap.search(None, 'FROM', 'axis.bank.in')[1]
eids = data[0].split()[:3]

def deep_unescape(s):
    # Repeatedly unescape HTML entities until stable
    prev = ""
    while prev != s:
        prev = s
        s = html.unescape(s)
    return s

for eid in eids:
    raw = imap.fetch(eid, '(RFC822)')[1][0][1]
    msg = email.message_from_bytes(raw)
    subject = decode_header(msg.get('Subject', ''))[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode(errors='ignore')
    
    # Get HTML part
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    html_body = part.get_payload(decode=True).decode()
                    break
                except:
                    continue
    else:
        try:
            html_body = msg.get_payload(decode=True).decode()
        except:
            pass
    
    if not html_body:
        continue
    
    # Decode nested entities
    text = deep_unescape(html_body)
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    print("=== EMAIL ===")
    print(f"Subject: {subject}")
    print(f"Body (first 1000 chars):\n{text[:1000]}\n{'='*50}\n")

imap.logout()
