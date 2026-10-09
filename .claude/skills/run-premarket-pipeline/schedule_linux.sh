#!/usr/bin/env bash
# Schedule the premarket pipeline on Linux/macOS (cron), weekdays.
# Usage:
#   ./schedule_linux.sh              # install at 08:15 ET
#   ./schedule_linux.sh 08:00        # different Eastern time
#   ./schedule_linux.sh 08:15 --prompt "Focus on semiconductors" --tickers NVDA,AMD --lang english
#                                    # everything after the time is passed to run_pipeline.py on every run
#   ./schedule_linux.sh --remove     # delete the entry
# The cron entry sets TZ=America/New_York for the job, so DST is handled by the system.
# Needs: a working `claude` on PATH, the project venv (.venv) with the packages installed.
set -euo pipefail

TAG="# premarket-pipeline"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$ROOT/.claude/skills/run-premarket-pipeline/run_pipeline.py"

current="$(crontab -l 2>/dev/null || true)"
others="$(printf '%s\n' "$current" | grep -v "$TAG" | grep -v '^CRON_TZ=America/New_York$' || true)"

if [ "${1:-}" = "--remove" ]; then
    printf '%s\n' "$others" | crontab -
    echo "Removed premarket pipeline cron entry"
    exit 0
fi

TIME="08:15"
if [[ "${1:-}" =~ ^[0-9]{1,2}:[0-9]{2}$ ]]; then TIME="$1"; shift; fi
PIPE_ARGS=""
for a in "$@"; do PIPE_ARGS+=" $(printf '%q' "$a")"; done   # keeps quotes safe inside the cron line
HH="${TIME%%:*}"; MM="${TIME##*:}"
PY="$ROOT/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
# cron runs with a minimal PATH, so pass the directory that holds `claude`
CLAUDE_DIR="$(dirname "$(command -v claude || echo /usr/local/bin/claude)")"

{
    printf '%s\n' "$others"
    echo "CRON_TZ=America/New_York"
    echo "$((10#$MM)) $((10#$HH)) * * 1-5 cd $ROOT && PATH=$CLAUDE_DIR:/usr/local/bin:/usr/bin:/bin $PY $SCRIPT$PIPE_ARGS >> $ROOT/logs/cron.log 2>&1 $TAG"
} | crontab -

mkdir -p "$ROOT/logs"
echo "Scheduled weekdays at $TIME ET${PIPE_ARGS:+ with:$PIPE_ARGS}. Check:  crontab -l"
echo "Logs: $ROOT/logs/pipeline_<date>.log (and cron.log for startup errors)"
echo "Note: CRON_TZ needs cronie or a similar cron. If your cron ignores it, convert $TIME ET to local time and edit the entry."
