#!/usr/bin/env bash
set -euo pipefail

cd /home/mmm/code/Mom/Subaru
mkdir -p logs

echo "=== [$(date '+%Y-%m-%d %H:%M:%S %Z %z')] Cricket daily search started ==="
python3 -B -m cricket run --manual
latest_report=$(find reports -maxdepth 1 -type f -name '*_crosstrek_search_report.md' -print | sort | tail -n 1)
python3 scripts/render_web_report.py "$latest_report"

if ! git diff --quiet HEAD -- docs/index.html; then
  git add docs/index.html
  git commit --only -m "Update Cricket report for $(date '+%Y-%m-%d')" -- docs/index.html
  git push origin HEAD:main
  echo "Cricket published the latest report to GitHub Pages."
else
  echo "Cricket report page already matches the latest report."
fi

echo "=== [$(date '+%Y-%m-%d %H:%M:%S %Z %z')] Cricket daily search finished ==="
