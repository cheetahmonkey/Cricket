#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT=/home/mmm/code/Mom/Subaru
HEALTHCHECK_URL_FILE=${CRICKET_HEALTHCHECK_URL_FILE:-/home/mmm/.config/cricket/healthchecks_url}
DAILY_RUNNER=${CRICKET_DAILY_RUNNER:-$REPOSITORY_ROOT/scripts/run_daily_cricket.sh}

healthcheck_url=""
if [[ -r "$HEALTHCHECK_URL_FILE" ]]; then
  IFS= read -r healthcheck_url < "$HEALTHCHECK_URL_FILE" || true
  healthcheck_url=${healthcheck_url%$'\r'}
  healthcheck_url=${healthcheck_url%/}
fi

healthcheck_enabled=false
if [[ "$healthcheck_url" == https://hc-ping.com/* && "$healthcheck_url" != *[[:space:]]* ]]; then
  healthcheck_enabled=true
else
  echo "Cricket healthcheck warning: ping URL is missing or invalid; continuing without monitoring." >&2
fi

healthcheck_ping() {
  local suffix=${1:-}
  local event=${2:-status}
  if [[ "$healthcheck_enabled" != true ]]; then
    return 0
  fi

  if ! curl -fsS -m 10 --retry 5 -o /dev/null "${healthcheck_url}${suffix}"; then
    echo "Cricket healthcheck warning: could not send ${event} ping; continuing." >&2
  fi
  return 0
}

report_failure_on_exit() {
  local status=$?
  trap - EXIT
  if (( status != 0 )); then
    healthcheck_ping "/${status}" "failure"
  fi
  exit "$status"
}

trap report_failure_on_exit EXIT

healthcheck_ping "/start" "start"
/bin/bash "$DAILY_RUNNER"
healthcheck_ping "" "success"

trap - EXIT
