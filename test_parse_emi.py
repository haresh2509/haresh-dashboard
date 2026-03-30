#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/haresh/.openclaw/workspace/skills/gmail-inbox-scan/scripts')
from expense_parser import parse_axis_email

body = """Transaction Info: UPI/123456789012/LOAN_REPAYMENT/EMI
Date & Time: 15-03-2025 10:30:00
Rs. 25,000.00 was debited from your A/c ending 1234.
"""

subject = "Payment credited to your Loan account no. XX3874"

result = parse_axis_email(body, subject)
print("EMI test result:", result)

# Also test normal debit
body2 = """Transaction Info: UPI/123456789012/ZOMATO/ORDER
Date & Time: 20-03-2025 14:45:00
Rs. 423.20 was debited from your A/c ending 1234."""
subject2 = "Debit transaction alert for Axis Bank A/c"
result2 = parse_axis_email(body2, subject2)
print("Normal debit test:", result2)
