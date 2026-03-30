#!/usr/bin/env python3
import os, imaplib, email, re, html
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

data = imap.search(None, 'FROM', 'axis.bank.in')[1]
eids = data[0].split()[:1]  # just first

def deep_unescape(s):
    prev = ""
    while prev != s:
        prev = s
        s = html.unescape(s)
    return s

for eid in eids:
    raw = imap.fetch(eid, '(RFC822)')[1][0][1]
    msg = email.message_from_bytes(raw)
    subject = decode_header(msg.get('Subject', ''))[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode(errors='ignore')
    
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    html_body = part.get_payload(decode=True).decode()
                    break
                except:
                    continue
    else:
        try:
            html_body = msg.get_payload(decode=True).decode()
        except:
            pass
    
    if not html_body:
        continue
    
    # decode entities
    text = deep_unescape(html_body)
    # strip tags but preserve some structure: keep table cell contents
    # Instead of stripping all tags, extract text from <td>, <p>, <span>
    # Use a simple regex to get visible text
    # Remove style/script blocks
    text = re.sub(r'(?is)<(style|script)[^>]*>.*?</\1>', '', text)
    # Replace common delimiters with newlines
    text = re.sub(r'<br\s*/?>|</p>|</div>|</tr>|</td>', '\n', text)
    # Remove remaining tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Unescape again
    text = html.unescape(text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Save to file for inspection
    with open('/tmp/axis_body.txt', 'w', encoding='utf-8') as f:
        f.write(f"Subject: {subject}\n\n")
        f.write(text)
    
    print("Saved to /tmp/axis_body.txt (length)", len(text))

imap.logout()
