#!/usr/bin/env bash
# Remove the premarket pipeline cron entry on Linux/macOS.
# Usage: ./unschedule_linux.sh
# Only the entry tagged "# premarket-pipeline" (and its CRON_TZ line) is removed.
# Your other cron jobs, reports, logs and .env are left alone.
set -euo pipefail

TAG="# premarket-pipeline"
current="$(crontab -l 2>/dev/null || true)"

if ! printf '%s\n' "$current" | grep -q "$TAG"; then
    echo "No premarket pipeline cron entry found. Nothing to remove."
    exit 0
fi

others="$(printf '%s\n' "$current" | grep -v "$TAG" | grep -v '^CRON_TZ=America/New_York$' || true)"
if [ -n "$others" ]; then
    printf '%s\n' "$others" | crontab -
else
    crontab -r
fi
echo "Removed the premarket pipeline cron entry. Check with: crontab -l"
