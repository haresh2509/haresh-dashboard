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

# Search for Axis alerts
data = imap.search(None, 'FROM', 'axis.bank.in')[1]
if not data or not data[0]:
    print("No messages from axis.bank.in")
else:
    eids = data[0].split()
    print(f"Found {len(eids)} Axis messages")
    eid = eids[0]
    raw = imap.fetch(eid, '(RFC822)')[1][0][1]
    msg = email.message_from_bytes(raw)
    frm = msg.get('From', '')
    subject = email.header.decode_header(msg.get('Subject', ''))[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode()
    print(f"From: {frm}")
    print(f"Subject: {subject}")
    print("----- BODY -----")
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
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
    print(body[:2000])
imap.logout()
