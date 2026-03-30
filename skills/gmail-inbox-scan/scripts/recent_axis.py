#!/usr/bin/env python3
import os, imaplib, email, re, html, datetime

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
if status != 'OK' or not data[0]:
    print("No recent Axis emails")
else:
    eid = data[0].split()[0]
    raw = imap.fetch(eid, '(RFC822)')[1][0][1]
    msg = email.message_from_bytes(raw)

    # Extract body like parser
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                try:
                    cand = part.get_payload(decode=True).decode()
                    if cand.strip():
                        body = cand
                        break
                except:
                    pass
            elif ct == "text/html" and not body:
                try:
                    html_raw = part.get_payload(decode=True).decode()
                    body = re.sub(r'<[^>]+>', ' ', html_raw)
                    body = re.sub(r'\s+', ' ', body).strip()
                    body = html.unescape(body)
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            pass

    # Show snippet around Date
    m = re.search(r'Date.*Time', body, re.IGNORECASE)
    if m:
        start = max(0, m.start()-50)
        end = min(len(body), m.end()+50)
        print("Context:", body[start:end])
    else:
        print("Date & Time not found. First 500 chars:")
        print(body[:500])

imap.logout()
