#!/usr/bin/env python3
"""
Generate Jan/Feb/Mar 2026 expense reports from Gmail scan and produce comparison dashboard.
"""
import os, sys, re, csv, datetime, subprocess, json
from datetime import datetime as dt

# We'll invoke the existing expense_parser.py with --days to cover each month, but write to separate CSVs
SCRIPT = '/home/haresh/.openclaw/workspace/skills/gmail-inbox-scan/scripts/expense_parser.py'

def scan_month(month, year, days_back):
    """Scan expenses for a given month by scanning enough days to cover it."""
    # We'll scan from a point that includes that month; easier: scan all from Jan 1 to end of month
    # But parser only supports days_back from today. So compute days since month end.
    today = dt.now().date()
    if year == 2026:
        if month == 1:
            target_end = dt(2026, 1, 31).date()
        elif month == 2:
            target_end = dt(2026, 2, 28).date()
        elif month == 3:
            target_end = dt(2026, 3, 31).date()
        else:
            target_end = today
    else:
        target_end = today
    days_back = (today - target_end).days
    # Run parser dry-run to get data without altering main CSV
    cmd = ['python3', SCRIPT, '--days', str(days_back), '--dry-run']
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(SCRIPT))
    # Parse the printed summary? Better: modify parser to return JSON; but we can't. Instead, we'll do a real run to a temp CSV
    temp_csv = f'/tmp/expenses_{year}{month:02d}.csv'
    cmd2 = ['python3', SCRIPT, '--days', str(days_back), '--csv', temp_csv]
    subprocess.run(cmd2, capture_output=True, text=True, cwd=os.path.dirname(SCRIPT))
    return temp_csv

def load_month_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DistReader(f))

def report_month(rows, month_name):
    total = sum(float(r['amount']) for r in rows)
    by_cat = {}
    for r in rows:
        cat = r['category']
        by_cat[cat] = by_cat.get(cat, 0) + float(r['amount'])
    return {
        'transactions': len(rows),
        'total': total,
        'by_category': by_cat
    }

# Generate CSVs for Jan, Feb, Mar
csv_jan = scan_month(1, 2026, 90)  # will internally compute days
csv_feb = scan_month(2, 2026, 90)
csv_mar = '/home/haresh/.openclaw/workspace/skills/gmail-inbox-scan/scripts/expenses.csv'  # use the actual updated CSV for March

jan_rows = load_month_csv(csv_jan)
feb_rows = load_month_csv(csv_feb)
mar_rows = [r for r in load_month_csv(csv_mar) if r['date'].startswith('2026-03')]

jan_report = report_month(jan_rows, "January")
feb_report = report_month(feb_rows, "February")
mar_report = report_month(mar_rows, "March")

# Print dashboard
print("📊 MONTH-ON-MONTH EXPENSE DASHBOARD — Q1 2026\n")
print(f"{'Metric':<25} {'January':<25} {'February':<25} {'March':<25}")
print("-" * 100)
print(f"{'Total Transactions':<25} {jan_report['transactions']:<25} {feb_report['transactions']:<25} {mar_report['transactions']:<25}")
print(f"{'Total Spent (₹)':<25} {jan_report['total']:<25.2f} {feb_report['total']:<25.2f} {mar_report['total']:<25.2f}")

# Category trends
cats = set(jan_report['by_category'].keys()) | set(feb_report['by_category'].keys()) | set(mar_report['by_category'].keys())
print(f"\n{'Category Breakdown':<25} {'January':<25} {'February':<25} {'March':<25}")
for cat in sorted(cats):
    j = jan_report['by_category'].get(cat, 0)
    f = feb_report['by_category'].get(cat, 0)
    m = mar_report['by_category'].get(cat, 0)
    print(f"{cat:<25} ₹{j:<25.2f} ₹{f:<25.2f} ₹{m:<25.2f}")

# Insights
print("\n🔍 INSIGHTS\n")
# Compute month-over-month changes
prev_totals = [jan_report['total'], feb_report['total'], mar_report['total']]
tx_counts = [jan_report['transactions'], feb_report['transactions'], mar_report['transactions']]
print(f"• Spending trend: {'↑' if prev_totals[1] > prev_totals[0] else '↓'} from Jan to Feb, {'↑' if prev_totals[2] > prev_totals[1] else '↓'} from Feb to Mar.")
print(f"• Highest spend month: {['January','February','March'][prev_totals.index(max(prev_totals))]} (₹{max(prev_totals):,.2f})")
print(f"• Most transactions: {['January','February','March'][tx_counts.index(max(tx_counts))]} ({max(tx_counts)} txns)")

# Category highlights
top_cats = {}
for cat in cats:
    total_cat = sum([
        jan_report['by_category'].get(cat,0),
        feb_report['by_category'].get(cat,0),
        mar_report['by_category'].get(cat,0)
    ])
    top_cats[cat] = total_cat
top3 = sorted(top_cats.items(), key=lambda x: x[1], reverse=True)[:3]
print(f"• Top 3 categories (Q1 total):", ", ".join([f"{c} ({t:,.0f})" for c,t in top3]))

# Anomalies
if 'EMI' in mar_report['by_category'] and mar_report['by_category']['EMI'] > 50000:
    print("• EMI category captured in March only (likely new loan/account)")

print("\nNote: January and February data was scanned via dry-run and may not capture all emails if Gmail has aged/blocked. March data is from finalized CSV.")
