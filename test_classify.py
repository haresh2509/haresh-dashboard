#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/haresh/.openclaw/workspace')
from gmail_inbox_scan import classify_email  # import the function

# Test Axis Bank case
subject = "Beware of apps that steal money from account"
body = "Security alert regarding apps..."
from_addr = '"Axis Bank" <info@digital.axisbankmail.bank.in>'

actionable, urgency, category, is_promo = classify_email(subject, body, from_addr)
print(f"Axis Bank test -> actionable={actionable}, urgency={urgency}, category={category}, is_promo={is_promo}")

# Test MasterCard
subject2 = "Thank you for your application!"
body2 = ""
from_addr2 = "MasterCard People Services <mastercard@myworkday.com>"

a2, u2, c2, p2 = classify_email(subject2, body2, from_addr2)
print(f"MasterCard test -> actionable={a2}, urgency={u2}, category={c2}, is_promo={p2}")
