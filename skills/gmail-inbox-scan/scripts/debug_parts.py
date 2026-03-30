#!/usr/bin/env python3
import os, imaplib, email, datetime

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
since = (datetime.datetime.now() - datetime.timedelta(days=4)).strftime("%d-%b-%Y")
status, data = imap.search(None, f'(SINCE "{since}")', 'FROM', 'axis.bank.in')
eid = data[0].split()[0]
raw = imap.fetch(eid, '(RFC822)')[1][0][1]
msg = email.message_from_bytes(raw)

print("Is multipart:", msg.is_multipart())
for i, part in enumerate(msg.walk()):
    print(f"Part {i}: {part.get_content_type()}, size {len(part.get_payload(decode=True) or b'')}")
    if part.get_content_type() in ["text/plain", "text/html"]:
        payload = part.get_payload(decode=True)
        if payload:
            text = payload.decode(errors='ignore')
            print(f"  Sample ({part.get_content_type()}): {text[:200]}")
imap.logout()
