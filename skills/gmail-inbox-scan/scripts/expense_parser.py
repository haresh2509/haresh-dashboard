#!/usr/bin/env python3
import os
import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta
import csv
import json

# Load credentials
env_path = '/home/haresh/.openclaw/workspace/.env.gmail'
env_vars = {}
if os.path.isfile(env_path):
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                env_vars[k] = v.strip()

GMAIL_ADDRESS = env_vars.get('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = env_vars.get('GMAIL_APP_PASSWORD')

# Load category mapping
categories_file = os.path.join(os.path.dirname(__file__), 'categories.json')
if os.path.exists(categories_file):
    with open(categories_file) as f:
        CATEGORIES = json.load(f)
else:
    CATEGORIES = {
        "Food": ["swiggy", "zomato", "restaurant", "cafe", "food", "dine", "eat", "bistro", "dining"],
        "Transport": ["uber", "ola", "fuel", "toll", "metro", "rapido", "parking", "taxi", "cab"],
        "Shopping": ["amazon", "flipkart", "myntra", "retail", "store", "mall", "shopping", "purchase", "bazaar"],
        "Utilities": ["electricity", "mobile", "broadband", "gas", "recharge", "bill", "utility", "power", "internet"],
        "Entertainment": ["movie", "ticket", "netflix", "prime", "hotstar", "spotify", "music", "gaming", "concert"],
        "Healthcare": ["pharmacy", "hospital", "doctor", "clinic", "medical", "health", "diagnostic", "lab"],
        "Household": ["rent", "grocery", "bigbasket", "natures basket", "grocer", "provisions", "milk", "vegetables"],
        "Transfer": ["upi", "bank transfer", "paytm", "gpay", "phonepe", "transfer", "receive", "send money"],
        "Education": ["course", "udemy", "coursera", "book", "ebook", "tuition", "coaching"],
        "Travel": ["flight", "train", "bus", "hotel", "stay", "airbnb", "vacation", "holiday"]
    }

SENDERS = [
    "axis",  # Focus only on Axis Bank as per requirement
]

# Senders/patterns to EXCLUDE (HR, support, non-merchant)
EXCLUDE_SENDERS = [
    "hr", "human resources", "payroll", "talent", "careers", "recruitment",
    "servicenow", "zendesk", "ticket", "case",  # removed: alert, notification
    "noreply", "no-reply", "donotreply", "mailer-daemon"
]

# Keywords that indicate non-transaction emails (HR, support, marketing, etc.)
EXCLUDE_SUBJECT_KEYWORDS = [
    "case", "ticket", "hrc", "payroll", "salary", "appraisal",
    "policy", "newsletter", "announcement", "security",  # removed: alert, notification
    "password", "login", "otp", "verification"
]

def categorize(merchant):
    merchant_lower = merchant.lower()
    for cat, keywords in CATEGORIES.items():
        if any(k in merchant_lower for k in keywords):
            return cat
    return "Other"  # default, will be post-filtered for amount

def is_exclusion_candidate(frm, subject, body):
    """Check if email should be skipped as non-merchant/HR/alert"""
    combined = (frm + " " + subject + " " + body[:200]).lower()
    for pattern in EXCLUDE_SENDERS:
        if pattern in combined:
            return True
    for kw in EXCLUDE_SUBJECT_KEYWORDS:
        if kw in subject.lower():
            return True
    # Filter extreme amounts that look like salary/ refunds (>5 lakhs)
    amount_match = re.search(r"(?:Rs\.?|₹)?\s*([\d,]+\.?\d{2})", body)
    if amount_match:
        try:
            amt = float(amount_match.group(1).replace(',', ''))
            if amt > 500000:
                return True
        except:
            pass
    return False

def parse_axis_email(body, subject):
    """Parse Axis Bank transaction alerts (debit only)"""
    
    body_lower = body.lower()
    subject_lower = subject.lower()
    
    # EMI detection: "Payment credited to your Loan account" means EMI debit
    if "payment credited to your loan account" in subject_lower:
        amt_match = re.search(r"(?:rs\.?|₹|inr)\s*([\d,]+\.?\d{2})", body, re.IGNORECASE)
        if amt_match:
            amount = float(amt_match.group(1).replace(',', ''))
            # Parse date
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
                    date_str = m.group(1)
                    for fmt in ["%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"]:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            if fmt in ["%d/%m/%y", "%d-%m-%y"] and dt.year < 100:
                                if dt.year < 50:
                                    dt = dt.replace(year=dt.year+2000)
                                else:
                                    dt = dt.replace(year=dt.year+1900)
                            date = dt.strftime("%Y-%m-%d")
                            break
                        except:
                            continue
                    if date:
                        break
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            return {"amount": amount, "merchant": "Loan EMI", "date": date, "category": "EMI"}
    
    # Extract amount
    amt_match = re.search(r"(?:rs\.?|₹|inr)\s*([\d,]+\.?\d{2})", body, re.IGNORECASE)
    if not amt_match:
        return None
    try:
        amount = float(amt_match.group(1).replace(',', ''))
    except:
        return None
    
    # Filter credits - look for "credited" in subject or body (but EMI handled above)
    if "credited" in subject_lower or "refunded" in subject_lower or "credited" in body_lower:
        return None
    
    # Extract date - multiple patterns
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
            date_str = m.group(1)
            for fmt in ["%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if fmt in ["%d/%m/%y", "%d-%m-%y"] and dt.year < 100:
                        if dt.year < 50:
                            dt = dt.replace(year=dt.year+2000)
                        else:
                            dt = dt.replace(year=dt.year+1900)
                    date = dt.strftime("%Y-%m-%d")
                    break
                except:
                    continue
            if date:
                break
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract merchant from Transaction Info line
    merch = "Axis Bank"
    ti_match = re.search(r"Transaction Info:\s*(.*?)\s+If\s+this\s+transaction", body, re.IGNORECASE | re.DOTALL)
    if ti_match:
        ti_line = ti_match.group(1).strip()
        parts = ti_line.split('/')
        if len(parts) >= 3:
            # Usually format: TYPE/REF/MERCHANT/ORDERID or TYPE/REF/MERCHANT
            candidate = parts[2].strip()
            if candidate and candidate.upper() not in ["ORDER", "PAYMENT", "TRANSFER", "DEBIT"]:
                merch = candidate
        if merch == "Axis Bank" and len(parts) >= 4:
            candidate = parts[3].strip()
            if candidate and candidate.upper() not in ["ORDER", "PAYMENT", "TRANSFER", "DEBIT"]:
                merch = candidate
    if merch == "Axis Bank":
        at_match = re.search(r"at\s+([A-Za-z0-9\s\.\-]+?)(?:\s+on|\s|$)", body, re.IGNORECASE)
        if at_match:
            merch = at_match.group(1).strip(" .,:-;")
            if merch.upper() in ["WEB", "CHAT", "SUPPORT", "CALL", "US"]:
                merch = "Axis Bank"
    
    category = categorize(merch)
    return {"amount": amount, "merchant": merch, "date": date, "category": category}

def parse_generic_email(body, subject):
    amount_match = re.search(r"(?:Rs\.?|₹)?\s*([\d,]+\.?\d{2})", body)
    date_match = re.search(r"(\d{1,2}[/-][A-Za-z]{3}[/-]\d{4})|(\d{4}-\d{2}-\d{2})", body)
    if amount_match:
        amount = float(amount_match.group(1).replace(',', ''))
        date_str = date_match.group(0) if date_match else datetime.now().strftime("%Y-%m-%d")
        try:
            if '/' in date_str or '-' in date_str and not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                for fmt in ["%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        date = datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                        break
                    except:
                        date = datetime.now().strftime("%Y-%m-%d")
            else:
                date = date_str
        except:
            date = datetime.now().strftime("%Y-%m-%d")
        merchant = "Unknown"
        for line in body.split('\n')[:5]:
            if any(k in line.lower() for k in ["at", "from", "merchant", "payee"]):
                words = line.split()
                if len(words) > 2:
                    merchant = " ".join(words[2:5])
                    break
        return {"amount": amount, "merchant": merchant, "date": date, "category": categorize(merchant)}
    return None

def load_processed_ids(state_file):
    processed_ids = set()
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    processed_ids.add(line)
    return processed_ids

def save_processed_ids(state_file, new_ids):
    # Append only unique new IDs
    existing = load_processed_ids(state_file)
    to_add = [nid for nid in new_ids if nid not in existing]
    if to_add:
        with open(state_file, 'a') as f:
            for nid in to_add:
                f.write(nid + '\n')
    return len(to_add)

def load_existing_expenses(csv_path):
    """Load existing expenses to deduplicate (date,merchant,amount)"""
    existing = set()
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['date'].strip(), row['merchant'].strip(), row['amount'].strip())
                existing.add(key)
    return existing

def is_duplicate_expense(expense, existing_set):
    """Check if expense already exists in CSV"""
    key = (expense['date'].strip(), expense['merchant'].strip(), str(expense['amount']).strip())
    return key in existing_set

def scan_expenses(days_back=1, csv_path=None, dry_run=False, verbose=False, folder="INBOX"):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise ValueError("Gmail credentials missing in .env.gmail")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if csv_path is None:
        csv_path = os.path.join(script_dir, 'expenses.csv')
    # Use separate state file per folder to avoid cross-contamination
    safe_folder = re.sub(r'[^A-Za-z0-9]', '_', folder)
    state_file = os.path.join(script_dir, f'.processed_ids_{safe_folder}.txt')

    # Load state
    processed_ids = load_processed_ids(state_file)
    existing_expenses = load_existing_expenses(csv_path)

    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    imap.select(folder)

    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
    status, data = imap.search(None, f'(SINCE "{since_date}")')
    if status != 'OK':
        print("Search failed")
        return []

    email_ids = data[0].split()
    print(f"Scanning {len(email_ids)} emails from last {days_back} day(s)...")
    expenses = []
    new_ids = []
    skipped_exclusions = 0
    skipped_duplicates = 0
    processed = 0

    for eid in email_ids:
        status, msg_data = imap.fetch(eid, '(RFC822)')
        if status != 'OK':
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        msg_id = msg.get('Message-ID', '').strip()
        if msg_id and msg_id in processed_ids:
            continue

        frm = msg.get('From', '')
        subject = decode_header(msg.get('Subject', ''))[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode(errors='ignore')
        subject = subject.strip()

        if verbose:
            print(f"  [DEBUG] MsgID: {msg_id[:20] if msg_id else 'N/A'}... From: {frm[:50] if frm else 'N/A'} | Subject: {subject[:80] if subject else 'N/A'}")

        # Quick sender filter
        if not any(s in frm.lower() for s in SENDERS):
            if verbose:
                print(f"    [SKIP] Sender not in SENDERS list")
            if msg_id:
                new_ids.append(msg_id)
            continue

        # Extract body (prefer text/plain; fallback to text/html stripped)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    try:
                        candidate = part.get_payload(decode=True).decode()
                        if candidate.strip():
                            body = candidate
                            break
                    except:
                        pass
                elif ctype == "text/html" and not body:
                    try:
                        html = part.get_payload(decode=True).decode()
                        body = re.sub(r'<[^>]+>', ' ', html)
                        body = re.sub(r'\s+', ' ', body).strip()
                        body = html.unescape(body)
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                pass

        body_lower = body.lower()

        # Exclude obvious non-merchant emails
        if is_exclusion_candidate(frm, subject, body):
            skipped_exclusions += 1
            if verbose:
                print(f"    [EXCLUDE] Matched exclusion pattern")
            if msg_id:
                new_ids.append(msg_id)
            continue

        # Parse - use Axis parser if from contains 'axis'
        expense = None
        frm_lower = frm.lower()
        if "axis" in frm_lower:
            expense = parse_axis_email(body, subject)
            if verbose and not expense:
                print(f"    [PARSE FAIL] Axis parser didn't match")
        else:
            expense = parse_generic_email(body, subject)
            if verbose and not expense:
                print(f"    [PARSE FAIL] Generic parser didn't match")

        if expense:
            # Post-filter: "Other" should only include small UPI/p2p transfers <= 250
            if expense["category"] == "Other" and float(expense["amount"]) > 250:
                expense["category"] = "Uncategorized"
            
            # Deduplicate against existing CSV
            if is_duplicate_expense(expense, existing_expenses):
                skipped_duplicates += 1
                if verbose:
                    print(f"    [DUPLICATE] {expense['date']} {expense['merchant']} ₹{expense['amount']}")
            else:
                expense["source"] = frm
                expense["subject"] = subject
                expenses.append(expense)
                existing_expenses.add((expense['date'].strip(), expense['merchant'].strip(), str(expense['amount']).strip()))
                if verbose:
                    print(f"    [ADD] {expense['date']} {expense['merchant']} ₹{expense['amount']} ({expense['category']})")

        if msg_id:
            new_ids.append(msg_id)

        processed += 1
        if processed % 100 == 0:
            print(f"Processed {processed}/{len(email_ids)}...")

    imap.logout()

    if dry_run:
        print(f"[DRY RUN] Would add {len(expenses)} expenses, skip {skipped_duplicates} duplicates, exclude {skipped_exclusions}")
        return expenses

    # Write to CSV
    if csv_path is None:
        csv_path = os.path.join(script_dir, 'expenses.csv')
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "merchant", "amount", "category", "source", "subject"])
        if not file_exists:
            writer.writeheader()
        for exp in expenses:
            writer.writerow(exp)

    # Save state (only after successful write)
    saved = save_processed_ids(state_file, new_ids)

    # Clean summary for Telegram (only stats)
    total = sum(e["amount"] for e in expenses)
    by_cat = {}
    for e in expenses:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
    
    if expenses:
        summary = [
            f"📊 *Expense Scan* ({datetime.now().strftime('%d %b %H:%M')})",
            f"✅ Added: ₹{total:,.2f} across {len(expenses)} transactions",
            "📂 Categories:"
        ]
        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            summary.append(f"  • {cat}: ₹{amt:,.2f}")
        summary.append(f"\n⏭️ Skipped: {skipped_duplicates} dupes, {skipped_exclusions} alerts")
    else:
        summary = [
            f"📊 *Expense Scan* ({datetime.now().strftime('%d %b %H:%M')})",
            "✅ No new expenses found."
        ]

    print("\n".join(summary))
    return expenses

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scan Gmail for expense emails and log to CSV")
    parser.add_argument("--days", type=int, default=1, help="Look back N days")
    parser.add_argument("--csv", default=None, help="CSV output path")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed debug output")
    parser.add_argument("--folder", default="INBOX", help="IMAP folder to scan (e.g., INBOX, '[Gmail]/All Mail')")
    args = parser.parse_args()

    # Pass folder to scan_expenses (need to modify function signature)
    # Temporarily: we'll override the select() inside scan_expenses by patching the call
    # For now, we'll modify scan_expenses to accept folder param
    exps = scan_expenses(days_back=args.days, csv_path=args.csv, dry_run=args.dry_run, verbose=args.verbose, folder=args.folder)
    if not args.dry_run:
        print(f"\n📝 Total new transactions added: {len(exps)}")
