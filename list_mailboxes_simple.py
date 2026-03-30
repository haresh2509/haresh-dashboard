#!/usr/bin/env python3
import imaplib, os, sys
env_path = '/home/haresh/.openclaw/workspace/.env.gmail'
env = {}
with open(env_path) as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v.strip()
try:
    imap = imaplib.IMAP4_SSL('imap.gmail.com')
    imap.login(env['GMAIL_ADDRESS'], env['GMAIL_APP_PASSWORD'])
    imap.list()
    status, mailboxes = imap.list()
    print("Mailboxes:")
    if status == 'OK':
        for mb in mailboxes:
            print(mb.decode())
    else:
        print("List failed", status)
    imap.logout()
except Exception as e:
    print("Error:", e, file=sys.stderr)
