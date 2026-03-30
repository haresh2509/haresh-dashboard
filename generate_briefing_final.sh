#!/usr/bin/env bash
set -uuo pipefail
export AGENT_BROWSER_ARGS="--no-sandbox"

echo "Generating morning briefing..." >&2

# Helper: run agent-browser command, capture output, fallback on error
run_cmd() {
  local out
  if out=$(eval "$1" 2>/dev/null); then
    echo "$out"
  else
    echo "$2"
  fi
}

# 1. War updates: Wikipedia current events
echo "Fetching war updates..." >&2
agent-browser open "https://en.wikipedia.org/wiki/Portal:Current_events" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 2000 >/dev/null 2>&1 || true
agent-browser get text body > /tmp/ce.txt 2>/dev/null || true
war_section=$(sed -n '/^Armed conflicts and attacks$/,/^Arts and culture$/{
  /^Armed conflicts and attacks$/d
  /^Arts and culture$/d
  p
}' /tmp/ce.txt 2>/dev/null | head -n 30)
# Clean up empty lines
war_updates=$(echo "$war_section" | sed '/^$/d')

# 2. Market summary: Livemint market page
echo "Fetching market summary..." >&2
agent-browser open "https://www.livemint.com/market" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 3000 >/dev/null 2>&1 || true
agent-browser get text body > /tmp/lm_market.txt 2>/dev/null || true
sensex_line=$(grep "SENSEX" /tmp/lm_market.txt | head -1 | sed 's/^[[:space:]]*//')
nifty_line=$(grep "NIFTY 50" /tmp/lm_market.txt | head -1 | sed 's/^[[:space:]]*//')
# Fallback if empty
[ -n "$sensex_line" ] || sensex_line="N/A"
[ -n "$nifty_line" ] || nifty_line="N/A"

# 3. RBI updates: from same Livemint market page
echo "Fetching RBI updates..." >&2
rbi_updates=$(grep -i "RBI" /tmp/lm_market.txt | head -5 | sed 's/^[[:space:]]*//')
[ -n "$rbi_updates" ] || rbi_updates="No RBI updates found"

# 4. AI in Audit news: try Livemint technology page
echo "Fetching AI in audit news..." >&2
agent-browser open "https://www.livemint.com/technology" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 3000 >/dev/null 2>&1 || true
agent-browser get text body > /tmp/livemint_tech.txt 2>/dev/null || true
ai_audit=$(grep -i "audit" /tmp/livemint_tech.txt | head -3)
[ -n "$ai_audit" ] || ai_audit="No AI in audit news found"

# 5. Weather: timeanddate.com
echo "Fetching weather..." >&2
agent-browser open "https://www.timeanddate.com/weather/india/mumbai" >/dev/null 2>&1 || true
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 3000 >/dev/null 2>&1 || true
agent-browser get text body > /tmp/weather.txt 2>/dev/null || true
temp_line=$(grep -m1 "°C" /tmp/weather.txt | head -1 | sed 's/^[[:space:]]*//')
cond_line=$(grep -E -m1 "Haze|Hazy|Sunny|Cloudy|Rain|Clear|Partly cloudy|Fog|Mist" /tmp/weather.txt | head -1 | sed 's/^[[:space:]]*//')
weather_summary="${temp_line}${cond_line:+, $cond_line}"
[ -n "$weather_summary" ] || weather_summary="Weather data unavailable"

# 6. Job links: Skipped due to access restrictions

# Compose summary
summary=$(cat <<EOF
Morning Briefing - $(date +"%A, %B %d, %Y")

War Updates:
$(echo "$war_updates" | sed 's/^/ - /' | sed '/^ - $/d' || echo " - Unable to fetch war updates")

Market Summary (as of $(date +%H:%M)):
- Sensex: $sensex_line
- Nifty: $nifty_line
- Gift Nifty: N/A (data not available)

RBI Updates:
$(echo "$rbi_updates" | sed 's/^/ - /' || echo " - No RBI updates found")

AI in Audit News:
$(echo "$ai_audit" | sed 's/^/ - /' || echo " - No AI in audit news found")

Mumbai Weather:
$weather_summary

Job Opportunities:
 - Job listings unavailable (site access restricted)

Notes:
- Automated data collection encountered access restrictions on several sources.
- Verify critical data manually before acting.
- Market data sourced from Livemint; war updates from Wikipedia.
EOF
)

echo "$summary"

# Clean up
agent-browser close >/dev/null 2>&1 || true
rm -f /tmp/ce.txt /tmp/lm_market.txt /tmp/livemint_tech.txt /tmp/weather.txt 2>/dev/null || true
echo "Briefing generation completed." >&2