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
msg = email.message_from_bytes(raw)

def walk(msg, indent=0):
    print("  " * indent + msg.get_content_type() + (f" name={msg.get_filename()}" if msg.get_filename() else ""))
    if msg.is_multipart():
        for part in msg.walk():
            # don't walk again for multipart/*
            if part.get_content_maintype() == 'multipart':
                continue
            walk(part, indent+1)

walk(msg)
imap.logout()
