#!/usr/bin/env bash
# Keep pipeline_main.py alive: restart it if it hangs or crashes.
# Every step is ledger-based and resume-safe, so a restart never repeats
# work (downloads, ingests or measurements).
#
# Usage:
#   scripts/run_pipeline.sh                    # run forever (restart every 4h)
#   RESTART_SECS=1800 scripts/run_pipeline.sh  # more aggressive restarts
#   scripts/run_pipeline.sh --limit 10         # args pass through; exits when done
#
# Stop it with:  touch results/.pipeline.stop  (or just kill this script)

cd "$(dirname "$0")/.." || exit 1
mkdir -p results
LOG=results/pipeline.log
RESTART_SECS="${RESTART_SECS:-14400}"

echo "[run_pipeline.sh] supervisor started (restart every ${RESTART_SECS}s max)" >> "$LOG"
while true; do
  if [ -f results/.pipeline.stop ]; then
    echo "[run_pipeline.sh] results/.pipeline.stop present — stopping supervisor" >> "$LOG"
    rm -f results/.pipeline.stop
    break
  fi
  echo "[run_pipeline.sh] $(date -u +%FT%TZ) starting pipeline_main.py $*" >> "$LOG"
  timeout --signal=TERM --kill-after=60 "$RESTART_SECS" \
    python3 scripts/pipeline_main.py "$@" >> "$LOG" 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[run_pipeline.sh] pipeline finished cleanly (rc=0) — supervisor exiting" >> "$LOG"
    break
  fi
  echo "[run_pipeline.sh] pipeline exited rc=$rc — restarting in 10s" >> "$LOG"
  sleep 10
done
