#!/usr/bin/env bash
set -uuo pipefail

# Required for running in container/VM without proper sandbox
export AGENT_BROWSER_ARGS="--no-sandbox"

echo "Starting morning briefing generation at $(date)" >&2

# Function to run agent-browser command with error fallback
run_agent_browser() {
  local cmd="$1"
  local fallback="$2"
  local output
  if output=$(eval "$cmd" 2>/dev/null); then
    echo "$output"
  else
    echo "$fallback"
  fi
}

# 1. War updates from Reuters World
echo "Fetching war updates..." >&2
agent-browser open "https://www.reuters.com/world/" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 3000 >/dev/null 2>&1 || true
war_headlines=$(run_agent_browser \
  'agent-browser eval --stdin <<'\''EOF'\''
JSON.stringify(
  Array.from(document.querySelectorAll('\''a[data-testid="Heading"], h3, h2'\''))
    .slice(0, 12)
    .map(el => el.innerText.trim())
    .filter(t => t.length > 0)
)
EOF' \
  '[]')
# Debug: Save raw headlines for inspection (optional)
# echo "$war_headlines" > /tmp/war_headlines.json

# 2. Market summary from Moneycontrol
echo "Fetching market summary..." >&2
agent-browser open "https://www.moneycontrol.com/markets/" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 3000 >/dev/null 2>&1 || true
market_data=$(run_agent_browser \
  'agent-browser eval --stdin <<'\''EOF'\''
(() => {
  const text = document.body.innerText;
  const sensex = text.match(/SENSEX\s*[:\s]*([\d,]+\.?\d*)/)?.[1] || null;
  const nifty = text.match(/NIFTY\s*[:\s]*([\d,]+\.?\d*)/)?.[1] || null;
  const giftNifty = text.match(/GIFT\s*NIFTY\s*[:\s]*([\d,]+\.?\d*)/i)?.[1] || null;
  return { sensex, nifty, giftNifty };
})()
EOF' \
  '{}')

# 3. RBI updates from official notifications page
echo "Fetching RBI updates..." >&2
agent-browser open "https://www.rbi.org.in/Scripts/BS_ViewMasNotifications.aspx" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 3000 >/dev/null 2>&1 || true
rbi_items=$(run_agent_browser \
  'agent-browser eval --stdin <<'\''EOF'\''
(() => {
  const rows = document.querySelectorAll('\''table#dg tr, table.grid tr, table tr'\'');
  const items = [];
  for (let i = 1; i < Math.min(rows.length, 6); i++) {
    const cells = rows[i].querySelectorAll('\''td'\'');
    if (cells.length >= 2) {
      items.push({
        date: cells[0].innerText.trim(),
        subject: cells[1].innerText.trim()
      });
    }
  }
  return items;
})()
EOF' \
  '[]')

# 4. AI in Audit news from Google News
echo "Fetching AI in audit news..." >&2
agent-browser open "https://news.google.com/search?q=AI+audit&hl=en-US&gl=US&ceid=US:en" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 3000 >/dev/null 2>&1 || true
ai_news=$(run_agent_browser \
  'agent-browser eval --stdin <<'\''EOF'\''
Array.from(document.querySelectorAll('\''article h3, h3[data-ved]'\''))
  .slice(0, 5)
  .map(h => h.innerText.trim())
  .filter(t => t.length > 0)
EOF' \
  '[]')

# 5. Mumbai weather from wttr.in
echo "Fetching weather..." >&2
agent-browser open "https://wttr.in/Mumbai?format=%C+%t+%h+%w" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
weather=$(agent-browser get text body 2>/dev/null | head -n1 | tr -d '\r' || echo "Weather data unavailable")

# 6. Job listings from Indeed
echo "Fetching job listings..." >&2
query="internal+audit|operational+risk|controls+testing|compliance|IFC|SOX+FP%26A+treasury"
location="Mumbai"
url="https://www.indeed.com/jobs?q=$query&l=$location&explvl=senior_level&fromage=15"
agent-browser open "$url" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 5000 >/dev/null 2>&1 || true
jobs_json=$(run_agent_browser \
  'agent-browser eval --stdin <<'\''EOF'\''
(() => {
  const jobs = Array.from(document.querySelectorAll('\''a.jcs-JobTitle, h2.jobTitle a'\''))
    .slice(0, 25)
    .map(a => ({
      title: a.innerText.trim(),
      url: a.href,
      company: (a.closest('\''div'\'')?.querySelector('\''span[data-testid="company-name"]'\'')?.innerText.trim() || '\'''\'')
    }));
  return jobs;
})()
EOF' \
  '[]')

# Filter jobs for target roles (case-insensitive)
filtered_jobs=$(echo "$jobs_json" | jq -r --argjson roles '["Internal Audit","Operational Risk","Controls Testing","Compliance","IFC","SOX","FP&A","Treasury"]' '
  map(select(
    (.title | ascii_downcase) as $t |
    any($roles[]; $t | contains(ascii_downcase))
  ))
' 2>/dev/null || echo '[]')

# 7. Compose the summary
summary=$(cat <<EOF
Morning Briefing - $(date +"%A, %B %d, %Y")

War Updates:
$(echo "$war_headlines" | jq -r '.[]?' 2>/dev/null | sed 's/^/ - /' || echo " - Unable to fetch war updates")

Market Summary (as of $(date +%H:%M)):
- Sensex: $(echo "$market_data" | jq -r '.sensex // "N/A"')
- Nifty: $(echo "$market_data" | jq -r '.nifty // "N/A"')
- Gift Nifty: $(echo "$market_data" | jq -r '.giftNifty // "N/A"')

RBI Updates:
$(echo "$rbi_items" | jq -r '.[]? | " - \(.date): \(.subject)"' 2>/dev/null || echo " - Unable to fetch RBI updates")

AI in Audit News:
$(echo "$ai_news" | jq -r '.[]?' 2>/dev/null | sed 's/^/ - /' || echo " - Unable to fetch AI audit news")

Mumbai Weather:
$weather

Job Opportunities (matching your profile - Senior Manager/AVP+ in Mumbai):
$(echo "$filtered_jobs" | jq -r '.[]? | " - \(.title) at \(.company)"' 2>/dev/null | head -n10 | sed 's/$/ - Apply: Indeed/' || echo " - No matching jobs found or unable to fetch")

Notes:
- Data collected via automated browsing. Verify details where critical.
- Job links include "Easy Apply" where available on platform.
EOF
)

# Output the summary
echo "$summary"

# Clean up
agent-browser close >/dev/null 2>&1 || true
echo "Briefing generation completed." >&2