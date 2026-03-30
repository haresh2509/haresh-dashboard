#!/usr/bin/env python3
import os, imaplib, email, html

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
eid = data[0].split()[0]
raw = imap.fetch(eid, '(RFC822)')[1][0][1]
msg = email.message_from_bytes(raw)

plain = ""
html_part = ""
if msg.is_multipart():
    for part in msg.walk():
        ct = part.get_content_type()
        if ct == "text/plain":
            try:
                plain = part.get_payload(decode=True).decode()
            except:
                pass
        elif ct == "text/html":
            try:
                html_part = part.get_payload(decode=True).decode()
            except:
                pass
else:
    plain = msg.get_payload(decode=True).decode()

print("=== PLAIN ===")
print(plain[:1000])
print("\n=== HTML (unescaped snippet) ===")
if html_part:
    # strip tags
    import re
    text = re.sub(r'<[^>]+>', ' ', html_part)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    print(text[:1000])
imap.logout()
