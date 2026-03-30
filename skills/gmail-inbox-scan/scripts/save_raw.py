#!/usr/bin/env python3
import os, imaplib, email

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

with open('/tmp/axis_email.eml', 'wb') as f:
    f.write(raw)

print("Saved raw email to /tmp/axis_email.eml")
imap.logout()
