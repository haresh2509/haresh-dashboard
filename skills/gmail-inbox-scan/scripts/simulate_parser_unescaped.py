#!/usr/bin/env python3
import email, re, html

with open('/tmp/axis_email.eml', 'rb') as f:
    raw = f.read()
msg = email.message_from_bytes(raw)

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

print("Body length:", len(body))
# Show first occurrence of "Date"
m = re.search(r'Date.*Time', body, re.IGNORECASE)
if m:
    start = max(0, m.start()-20)
    end = min(len(body), m.end()+30)
    print("Found:", body[start:end])

# Try date extract
date = None
date_patterns = [
    r"on\s+(\d{1,2}[/-][A-Za-z]{3}[/-]\d{4})",
    r"date\s*[:\-]?\s*(\d{1,2}[/-][A-Za-z]{3}[/-]\d{4})",
    r"Date\s*&\s*Time:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(\d{1,2}[/-][A-Za-z]{3}[/-]\d{2,4})",
    r"(\d{4}-\d{2}-\d{2})"
]
for pat in date_patterns:
    m = re.search(pat, body, re.IGNORECASE)
    if m:
        ds = m.group(1)
        print(f"Pattern '{pat}' matched: {ds}")
        for fmt in ["%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"]:
            try:
                from datetime import datetime as dt
                d = dt.strptime(ds, fmt)
                if fmt in ["%d/%m/%y", "%d-%m-%y"] and d.year < 100:
                    if d.year < 50:
                        d = d.replace(year=d.year+2000)
                    else:
                        d = d.replace(year=d.year+1900)
                date = d.strftime("%Y-%m-%d")
                print("Parsed as", date)
                break
            except:
                continue
        if date:
            break
if not date:
    print("No date parsed, default to today")
    date = dt.now().strftime("%Y-%m-%d")
    print(date)
