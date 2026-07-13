#!/usr/bin/env bash
set -euo pipefail

cd /home/mmm/code/Mom/Subaru
mkdir -p logs

echo "=== [$(date '+%Y-%m-%d %H:%M:%S %Z %z')] Cricket daily search started ==="
python3 -B -m cricket run --manual
echo "=== [$(date '+%Y-%m-%d %H:%M:%S %Z %z')] Cricket daily search finished ==="
