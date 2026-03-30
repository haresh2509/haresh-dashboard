#!/usr/bin/env python3
import os
import smtplib
import subprocess
from email.message import EmailMessage

def send_job_application(to_email, job_title, company="", recipient_name="", attachment_path=None):
    """Send a job application email from Haresh Mulchandani via Gmail SMTP."""

    from_email = os.getenv("GMAIL_ADDRESS", "haresh.mulchandani01@gmail.com")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not app_password:
        raise ValueError("GMAIL_APP_PASSWORD not set in environment")

    msg = EmailMessage()
    msg["Subject"] = f"Application: {job_title} ({company}) — Haresh Mulchandani, CA"
    msg["From"] = from_email
    msg["To"] = to_email

    body = f"""Dear {recipient_name or 'Hiring Manager'},

I am writing to express my interest in the {job_title} position as advertised.

I am a Chartered Accountant (2019) with 6+ years of post-qualification experience in Internal Audit, Operational Risk, and Financial Controls across leading banks:

• Current: Manager, FP&A — Citi Corp (Sept 2024–Present)
• Previous: Senior Manager, Internal Audit — Axis Bank (3 years)
• Previous: Deputy Manager, Operational Risk & Compliance — Yes Bank

My expertise spans IFC reviews, SOX compliance, controls testing, RBI/SEBI regulatory audit, and risk-based audit planning — directly aligned with the role's requirements.

Please find my resume attached. I would welcome the opportunity to discuss this further.

Best regards,
Haresh Mulchandani, CA
📞 +91 7021544904
📧 {from_email}
🔗 linkedin.com/in/haresh4744
"""

    msg.set_content(body)

    if attachment_path and os.path.isfile(attachment_path):
        with open(attachment_path, "rb") as f:
            filename = os.path.basename(attachment_path)
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=filename)
    else:
        # Optional: attach default resume if exists
        default_resume = os.path.expanduser("~/.openclaw/workspace/resumes/Resume_CA_HARESH_MULCHANDANI.pdf")
        if os.path.isfile(default_resume):
            with open(default_resume, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="Resume_CA_HARESH_MULCHANDANI.pdf")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(from_email, app_password)
        smtp.send_message(msg)

    print(f"✅ Email sent to {to_email}")

    # Auto-log to job tracker
    try:
        tracker_script = os.path.expanduser("~/.openclaw/skills/job-tracker/scripts/email-hook.js")
        subprocess.run([
            "node", tracker_script,
            "--company", company or "Unknown Company",
            "--role", job_title,
            "--method", "email",
            "--notes", f"Sent to {to_email}"
        ], check=False)
        print("📝 Application logged in tracker")
    except Exception as e:
        print(f"⚠️ Tracker logging failed: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: send_test.py <to_email> <job_title> [company] [recipient_name]")
        sys.exit(1)

    to_email = sys.argv[1]
    job_title = sys.argv[2]
    company = sys.argv[3] if len(sys.argv) > 3 else ""
    recipient_name = sys.argv[4] if len(sys.argv) > 4 else ""

    send_job_application(to_email, job_title, company, recipient_name)
