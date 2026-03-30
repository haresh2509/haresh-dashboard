#!/usr/bin/env python3
import imaplib, os, re, datetime
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

# List all labels (mailboxes)
status, mailboxes = imap.list()
print("Available mailboxes:")
for mb in mailboxes:
    # Decode and show name
    parts = mb.decode().split(' "/" ')
    if len(parts) >= 2:
        name = parts[1].replace('"', '')
        print(f" - {name}")
    else:
        print(mb.decode())

imap.logout()
