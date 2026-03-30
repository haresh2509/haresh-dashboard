#!/usr/bin/env python3
"""
Daily Self-Audit — check health of all cron jobs and services
"""
import os, json, datetime, subprocess, sys
from datetime import datetime as dt

CRON_JOBS = '/home/haresh/.openclaw/cron/jobs.json'
GATEWAY_STATUS = 'openclaw gateway status'

def check_gateway():
    try:
        out = subprocess.check_output(['openclaw', 'gateway', 'status'], text=True, timeout=10)
        return "running" in out.lower()
    except:
        return False

def check_cron_jobs():
    try:
        with open(CRON_JOBS) as f:
            jobs = json.load(f)
    except Exception as e:
        return f"Error reading cron jobs: {e}"
    
    now_ts = dt.now().timestamp() * 1000
    lines = []
    all_ok = True
    for job in jobs:
        name = job.get('name', 'Unknown')
        state = job.get('state', {})
        last_run = state.get('lastRunAtMs', 0)
        last_status = state.get('lastRunStatus', 'unknown')
        next_run = state.get('nextRunAtMs', 0)
        # If last run was > 24h ago, flag
        if last_run > 0:
            last_dt = dt.fromtimestamp(last_run/1000)
            hours_ago = (dt.now() - last_dt).total_seconds() / 3600
            if hours_ago > 24 and last_status != 'ok':
                lines.append(f"❌ {name}: last run {hours_ago:.1f}h ago, status={last_status}")
                all_ok = False
            else:
                lines.append(f"✅ {name}: last run {hours_ago:.1f}h ago, status={last_status}")
        else:
            lines.append(f"⚠️ {name}: never run")
            all_ok = False
    return "\n".join(lines), all_ok

def main():
    report = ["🔎 DAILY SELF-AUDIT", dt.now().strftime("%Y-%m-%d %H:%M"), ""]
    
    # Gateway
    gw_up = check_gateway()
    report.append(f"Gateway: {'✅ UP' if gw_up else '❌ DOWN'}")
    
    # Cron jobs
    report.append("\nCron Jobs Health:")
    job_report, jobs_ok = check_cron_jobs()
    report.append(job_report)
    
    if not gw_up or not jobs_ok:
        report.append("\n⚠️ Issues detected. Consider investigating.")
        # Could auto-restart gateway if down
        if not gw_up:
            subprocess.run(['openclaw', 'gateway', 'restart'], capture_output=True)
            report.append("🔁 Restarted gateway.")
    else:
        report.append("\n✅ All systems healthy.")
    
    print("\n".join(report))

if __name__ == "__main__":
    main()
