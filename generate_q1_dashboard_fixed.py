#!/usr/bin/env python3
"""
Q1 2026 Expense Dashboard — Single synchronous scan
"""
import os, csv, datetime, subprocess, sys
from datetime import datetime as dt

SCRIPT = '/home/haresh/.openclaw/workspace/skills/gmail-inbox-scan/scripts/expense_parser.py'
TEMP_CSV = '/tmp/expenses_Jan_to_Mar.csv'

# Compute days back to Jan 1 2026
today = dt.now().date()
jan1 = dt(2026, 1, 1).date()
days_back = (today - jan1).days + 1  # inclusive

# Clean any previous temp CSV and state to ensure full scan
if os.path.exists(TEMP_CSV):
    os.remove(TEMP_CSV)
state_file = os.path.join(os.path.dirname(SCRIPT), '.processed_ids.txt')
if os.path.exists(state_file):
    os.remove(state_file)

print(f"Scanning {days_back} days (Jan 1 → today)...")
cmd = ['python3', SCRIPT, '--days', str(days_back), '--csv', TEMP_CSV]
print('Running:', ' '.join(cmd))
result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(SCRIPT))
print(result.stdout)
if result.returncode != 0:
    print("Scan failed:", result.stderr)
    sys.exit(1)

# Load all rows
with open(TEMP_CSV, 'r', encoding='utf-8') as f:
    all_rows = list(csv.DictReader(f))

def get_month(date_str):
    try:
        return int(date_str.split('-')[1])
    except:
        return 0

jan_rows = [r for r in all_rows if get_month(r['date']) == 1]
feb_rows = [r for r in all_rows if get_month(r['date']) == 2]
mar_rows = [r for r in all_rows if get_month(r['date']) == 3]

def report(rows):
    total = sum(float(r['amount']) for r in rows)
    by_cat = {}
    for r in rows:
        by_cat[r['category']] = by_cat.get(r['category'], 0) + float(r['amount'])
    return {'tx': len(rows), 'total': total, 'cats': by_cat}

jan = report(jan_rows)
feb = report(feb_rows)
mar = report(mar_rows)

print("\n📊 Q1 2026 EXPENSE DASHBOARD\n")
print(f"{'Metric':<25} {'January':<25} {'February':<25} {'March':<25}")
print("-" * 100)
print(f"{'Total Transactions':<25} {jan['tx']:<25} {feb['tx']:<25} {mar['tx']:<25}")
print(f"{'Total Spent (₹)':<25} {jan['total']:<25.2f} {feb['total']:<25.2f} {mar['total']:<25.2f}")

all_cats = set(jan['cats'].keys()) | set(feb['cats'].keys()) | set(mar['cats'].keys())
print(f"\n{'Category':<25} {'January':<25} {'February':<25} {'March':<25}")
for cat in sorted(all_cats):
    j = jan['cats'].get(cat, 0)
    f = feb['cats'].get(cat, 0)
    m = mar['cats'].get(cat, 0)
    print(f"{cat:<25} ₹{j:<25.2f} ₹{f:<25.2f} ₹{m:<25.2f}")

# Insights
print("\n🔍 INSIGHTS\n")
print(f"• Spending {'↑' if feb['total']>jan['total'] else '↓'} Feb vs Jan; {'↑' if mar['total']>feb['total'] else '↓'} Mar vs Feb.")
print(f"• Highest spend month: {['January','February','March'][max(range(3), key=lambda i: [jan['total'],feb['total'],mar['total']][i])]} (₹{max([jan['total'],feb['total'],mar['total']]):,.2f})")
print(f"• Most transactions: {['January','February','March'][max(range(3), key=lambda i: [jan['tx'],feb['tx'],mar['tx']][i])]} ({max([jan['tx'],feb['tx'],mar['tx']])} txns)")

cat_totals = {}
for cat in all_cats:
    cat_totals[cat] = sum([jan['cats'].get(cat,0), feb['cats'].get(cat,0), mar['cats'].get(cat,0)])
top3 = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:3]
print(f"• Top 3 categories Q1: " + ", ".join([f"{c} ({t:,.0f})" for c,t in top3]))

if 'EMI' in mar['cats'] and mar['cats']['EMI'] > 50000:
    print(f"• EMI category appeared in March only: ₹{mar['cats']['EMI']:,.2f} (new loan/account)")

print("\nData source: Gmail (Axis Bank alerts) parsed by expense_parser.py")
print(f"Full CSV: {TEMP_CSV}")
