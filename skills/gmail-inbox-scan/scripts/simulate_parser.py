#!/usr/bin/env python3
import re, email

# Load raw email
with open('/tmp/axis_email.eml', 'rb') as f:
    raw = f.read()

msg = email.message_from_bytes(raw)

# Extract HTML part (same as parser)
html_body = ""
if msg.is_multipart():
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html_body = part.get_payload(decode=True).decode()
            break
else:
    html_body = msg.get_payload(decode=True).decode()

# Apply parser's exact fallback processing (no style stripping, no br newline)
body = re.sub(r'<[^>]+>', ' ', html_body)
body = re.sub(r'\s+', ' ', body).strip()

# Save for inspection
with open('/tmp/parser_body.txt', 'w', encoding='utf-8') as f:
    f.write(body)

print("Body length:", len(body))
# Show around "Transaction"
m = re.search(r'Transaction\s*Info', body, re.IGNORECASE)
if m:
    start = max(0, m.start()-50)
    end = min(len(body), m.end()+200)
    print("Found at position", m.start())
    print(body[start:end])
else:
    print("Transaction Info NOT found")
    # Show first 500 chars
    print(body[:500])
