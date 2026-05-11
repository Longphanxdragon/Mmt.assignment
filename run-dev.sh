#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "Starting sampleapp on port 9001..."
nohup bash -lc "cd '$ROOT_DIR/CO3094-asynaprous' && python3 start_sampleapp.py --server-port 9001" > "$LOG_DIR/sampleapp.log" 2>&1 &
echo $! > "$LOG_DIR/sampleapp.pid"
sleep 0.6

echo "Starting proxy on port 8080..."
nohup bash -lc "cd '$ROOT_DIR/CO3094-asynaprous' && python3 start_proxy.py --server-port 8080" > "$LOG_DIR/proxy.log" 2>&1 &
echo $! > "$LOG_DIR/proxy.pid"
sleep 0.6

echo "Services started. Logs: $LOG_DIR/sampleapp.log, $LOG_DIR/proxy.log"
echo "Tailing last 12 lines of each log:"
echo "---- sampleapp.log ----"
tail -n 12 "$LOG_DIR/sampleapp.log" || true
echo "---- proxy.log ----"
tail -n 12 "$LOG_DIR/proxy.log" || true
