# Security Action Plan — March 28, 2026

## Critical: Rotate These Immediately

### 1. Groq API Key
If you ever stored a Groq key in `.env`:
- Go to https://console.groq.com/keys
- Revoke any old/compromised keys
- Create a new key
- Update your config with `GROQ_API_KEY=<new_key>`

### 2. Gmail App Password
If you stored an app password in `.env.gmail`:
- Open Google Account → Security → App passwords
- Revoke the old password (it looks like: `xxxx xxxx xxxx xxxx`)
- Generate a new 16-char password
- Update your config with `GMAIL_APP_PASSWORD=<new_password>`

## Prevent Future Leaks

- `.env` and `.env.*` are now in `.gitignore` — never commit them.
- Use a password manager (`1password` CLI or `himalaya`) for secure retrieval.
- Keep a template `.env.example` with placeholder values only.

## Audit Findings (resolved)

- [x] `.env` removed from workspace
- [x] `.env.gmail` removed from workspace
- [x] `.gitignore` updated
- [x] `.env.example` template added
- [ ] Verify no secrets in git history (if you ever committed)

## Next Steps

After rotation:
1. Run security audit again: `./skills/proactive-agent/scripts/security-audit.sh`
2. Confirm no real warnings remain.
3. Consider enabling `1password` skill for future secret management.
