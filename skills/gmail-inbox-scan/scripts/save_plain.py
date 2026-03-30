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

plain = None
for part in msg.walk():
    if part.get_content_type() == "text/plain":
        plain = part.get_payload(decode=True).decode(errors='ignore')
        break

if plain:
    with open('/tmp/recent_plain.txt', 'w', encoding='utf-8') as f:
        f.write(plain)
    print("Plain saved, length", len(plain))
    # Show first 1000 chars
    print(plain[:1000])
else:
    print("No plain part")
imap.logout()
