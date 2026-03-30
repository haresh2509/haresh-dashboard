# Gmail Inbox Scan Skill

## Overview
Automatically scans Gmail inbox for expense emails (currently supports Axis Bank transaction alerts) and logs them to a CSV file.

## Setup

1. **Gmail App Password**
   - Use a Gmail account with 2FA enabled.
   - Generate an App Password (16-character) at https://myaccount.google.com/apppasswords
   - Create `.env.gmail` file in the skill directory with:
     ```
     GMAIL_ADDRESS=your.email@gmail.com
     GMAIL_APP_PASSWORD=your_app_password
     ```

2. **Categories Configuration**
   - Edit `categories.json` to adjust expense categories.
   - The parser uses keyword matching: if any keyword appears in the merchant name (case-insensitive), the expense is assigned that category.

3. **Install as Skill**
   - Place the files in `~/.openclaw/workspace/skills/gmail-inbox-scan/`
   - Ensure `expense_parser.py` is executable: `chmod +x expense_parser.py`

## Usage

```bash
# Scan last N days (default=1)
python3 expense_parser.py --days 4

# Dry run (preview without writing)
python3 expense_parser.py --days 4 --dry-run --verbose

# Custom CSV path
python3 expense_parser.py --csv /path/to/expenses.csv --days 7
```

## Output

- CSV columns: `date`, `merchant`, `amount`, `category`, `source`, `subject`
- Telegram summary (if run via OpenClaw): stats by category, totals, skip counts
- Duplicates are tracked via Message-ID and (date,merchant,amount) to avoid re-adding

## How It Works

1. Connects to Gmail via IMAP and searches for emails from Axis Bank (`axis.bank.in`) in the past N days.
2. Processes each email:
   - Prefers `text/plain` body if non-empty; falls back to `text/html` (strips tags and decodes entities).
   - Extracts amount (regex for Rs./INR).
   - Skips if subject/body indicates a credit transaction.
   - Extracts date (tries multiple patterns, handles 2-digit years).
   - Extracts merchant from `Transaction Info:` field (UPI/P2A/.../MERCHANT). Fallback to `at MERCHANT` pattern with footer word filtering.
   - Categorizes using `categories.json`.
3. Saves new transactions to `expenses.csv` (appends).
4. Marks processed emails by Message-ID to avoid duplicates on subsequent runs.
5. Prints a concise summary for Telegram.

## Notes

- Only **debit** transactions are captured; credits (refunds, income) are ignored.
- The parser is tuned for Axis Bank India transaction alerts. Other banks will require additional parsers.
- HTML emails are heavily encoded; the script performs deep unescaping.
- State is stored in `.processed_ids.txt` in the script directory.

## Integration

Add to OpenClaw cron (in your main session):
```
0 9 * * * /usr/bin/python3 /home/haresh/.openclaw/workspace/skills/gmail-inbox-scan/scripts/expense_parser.py --days 1
```
Or trigger via a custom OpenClaw command/skill.
