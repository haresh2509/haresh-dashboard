#!/usr/bin/env python3
"""
Add daily self-audit cron job to OpenClaw config.
"""
import json, os, time
from datetime import datetime as dt

cron_path = '/home/haresh/.openclaw/cron/jobs.json'
with open(cron_path) as f:
    jobs = json.load(f)

new_job = {
  "id": "c3d4e5f6-a7b8-9012-b3c4-d5e6f7a8b9c0",
  "name": "daily-self-audit",
  "enabled": True,
  "createdAtMs": int(time.time()*1000),
  "updatedAtMs": int(time.time()*1000),
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "Asia/Kolkata"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "Run daily self-audit: check gateway status, cron job health, and report any issues. Script at /home/haresh/.openclaw/workspace/daily_self_audit.py"
  },
  "delivery": {
    "mode": "announce",
    "channel": "default",
    "to": "654478564"
  },
  "state": {
    "nextRunAtMs": 0,
    "lastRunAtMs": 0,
    "lastRunStatus": "ok",
    "lastStatus": "ok",
    "lastDurationMs": 0,
    "lastDeliveryStatus": "pending",
    "consecutiveErrors": 0,
    "lastDelivered": False
  }
}

# Append if not exists
if not any(j.get('name') == 'daily-self-audit' for j in jobs):
    jobs.append(new_job)
    with open(cron_path, 'w') as f:
        json.dump(jobs, f, indent=2)
    print("Added daily-self-audit job")
else:
    print("Job already exists")
