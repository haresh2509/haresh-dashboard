#!/usr/bin/env python3
import os, imaplib, email, re
from email.header import decode_header
import html

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

# Fetch 5 recent Axis emails
data = imap.search(None, 'FROM', 'axis.bank.in')[1]
eids = data[0].split()[:5]

for eid in eids:
    raw = imap.fetch(eid, '(RFC822)')[1][0][1]
    msg = email.message_from_bytes(raw)
    frm = msg.get('From', '')
    subject = decode_header(msg.get('Subject', ''))[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode(errors='ignore')
    
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            pass
    
    if body:
        # Strip HTML
        text = re.sub(r'<[^>]+>', ' ', body)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        print("=== EMAIL ===")
        print(f"Subject: {subject}")
        print(f"Text (first 500 chars):\n{text[:500]}\n")

imap.logout()
