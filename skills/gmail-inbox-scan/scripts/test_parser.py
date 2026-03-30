#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/haresh/.openclaw/workspace/skills/gmail-inbox-scan/scripts')
from expense_parser import parse_axis_email

# Read the body we extracted earlier
with open('/tmp/axis_body.txt', 'r', encoding='utf-8') as f:
    full = f.read()
# Extract the body part after Subject line
lines = full.split('\n', 1)
if len(lines) > 1:
    body = lines[1]
else:
    body = full

result = parse_axis_email(body, "INR 1469.00 was debited from your A/c no. XX2267.")
print(result)
