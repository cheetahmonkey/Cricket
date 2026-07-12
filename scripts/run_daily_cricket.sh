#!/usr/bin/env bash
set -euo pipefail

cd /home/mmm/code/Mom/Subaru
mkdir -p logs

python3 -B -m cricket run --manual
