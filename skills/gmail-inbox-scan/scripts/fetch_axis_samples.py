#!/usr/bin/env python3
"""Deep diagnostic: fetch 2-3 Axis alert emails (raw HTML) to understand structure"""
import os, imaplib, email, re, json
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

# Fetch 3 recent Axis emails with full body
data = imap.search(None, 'FROM', 'axis.bank.in')[1]
eids = data[0].split()[:3]

samples = []
for eid in eids:
    raw = imap.fetch(eid, '(RFC822)')[1][0][1]
    msg = email.message_from_bytes(raw)
    frm = msg.get('From', '')
    subject = decode_header(msg.get('Subject', ''))[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode()
    
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
    
    samples.append({'subject': subject, 'body': body[:1000]})

imap.logout()

print(json.dumps(samples, indent=2, ensure_ascii=False))
