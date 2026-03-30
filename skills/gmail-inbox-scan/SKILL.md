---
name: gmail-inbox-scan
description: Scan Gmail inbox for actionable emails: job applications, urgent messages, and promotional content. Generates a report with draft replies for job-related emails only. Supports filtering by date range.
---

# Gmail Inbox Scanner

Scans Gmail for actionable emails and produces a concise report with suggested actions and draft replies (for job-related emails only).

## Capabilities

- Scan last N days (default: 1)
- Classify emails into: Job, Urgent, Official, Promotional
- Generate draft reply ONLY for Job category (not for Urgent/Official)
- Output report with actionable items, urgency, and draft texts
- Duplicate detection via Message-ID tracking (state stored in `.processed_ids.txt`)

## Usage

Run the scanner script:

```bash
python3 /home/haresh/.openclaw/workspace/skills/gmail-inbox-scan/scripts/inbox_scanner.py [--days N] [--dry-run] [--verbose]
```

The script prints a formatted report to stdout.

### Arguments

- `--days N`: Look back N days (default 1)
- `--dry-run`: Preview without marking emails as processed (still updates state file)
- `--verbose`: Show detailed debug output per email

## Output

Report includes:
- Total emails scanned
- Actionable items count
- For each actionable item: sender, subject, date, urgency, category, suggested actions
- Draft reply (only for Job category)

## Integration

Cron job `gmail-inbox-scan` runs every 3 hours and sends the report to Telegram. Do not modify the script's output format.

## Notes

- Only job-related emails get a draft reply. Urgent and Official emails are listed but without draft.
- Excludes known non-job senders (banks, HR platforms not related to recruitment).
- Uses Gmail IMAP; credentials stored in workspace `.env.gmail`.
