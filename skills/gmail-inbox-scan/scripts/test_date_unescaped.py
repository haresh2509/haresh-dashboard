#!/usr/bin/env python3
import re, html

body = open('/tmp/parser_body.txt', 'r', encoding='utf-8').read()
# Apply unescape as parser now does
body = html.unescape(body)

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
        print("Pattern matched:", pat)
        date_str = m.group(1)
        print("  date_str:", date_str)
        # try parse
        for fmt in ["%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"]:
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, fmt)
                if fmt in ["%d/%m/%y", "%d-%m-%y"] and dt.year < 100:
                    if dt.year < 50:
                        dt = dt.replace(year=dt.year + 2000)
                    else:
                        dt = dt.replace(year=dt.year + 1900)
                print("  parsed with", fmt, "->", dt.strftime("%Y-%m-%d"))
                break
            except:
                continue
        break

# Also show snippet around "Date &"
m2 = re.search(r"Date.*Time", body, re.IGNORECASE)
if m2:
    print("Context:", body[m2.start()-20:m2.end()+30])
