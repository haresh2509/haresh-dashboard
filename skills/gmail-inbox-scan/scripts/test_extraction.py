#!/usr/bin/env python3
"""Test extraction on a saved raw HTML email"""
import re, html

with open('/tmp/axis_email.eml', 'rb') as f:
    raw = f.read()

import email
msg = email.message_from_bytes(raw)
# Extract HTML
html_body = ""
if msg.is_multipart():
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html_body = part.get_payload(decode=True).decode()
            break
else:
    html_body = msg.get_payload(decode=True).decode()

# decode entities
def deep_unescape(s):
    prev = ""
    while prev != s:
        prev = s
        s = html.unescape(s)
    return s

text = deep_unescape(html_body)
text = re.sub(r'(?is)<(style|script)[^>]*>.*?</\1>', '', text)
text = re.sub(r'<br\s*/?>|</p>|</div>|</tr>|</td>', '\n', text)
text = re.sub(r'<[^>]+>', ' ', text)
text = html.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()

print("Length:", len(text))
# Search for Transaction
m = re.search(r"Transaction\s*Info", text, re.IGNORECASE)
print("Found Transaction Info:", bool(m))
if m:
    start = max(0, m.start()-50)
    end = min(len(text), m.end()+200)
    print(text[start:end])
