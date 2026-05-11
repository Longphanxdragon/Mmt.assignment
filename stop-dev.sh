#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"

kill_pidfile() {
  local pidfile="$1"
  if [[ -f "$pidfile" ]]; then
    pid=$(cat "$pidfile")
    if [[ -n "$pid" ]]; then
      echo "Killing PID $pid from $pidfile"
      kill "$pid" 2>/dev/null || true
      sleep 0.2
      if kill -0 "$pid" 2>/dev/null; then
        echo "Process $pid still alive, force killing"
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$pidfile"
  fi
}

kill_pidfile "$LOG_DIR/sampleapp.pid" || true
kill_pidfile "$LOG_DIR/proxy.pid" || true

echo "Stopped dev services. Logs remain in $LOG_DIR"
