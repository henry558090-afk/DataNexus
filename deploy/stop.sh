#!/usr/bin/env bash
# data-nexus 停止（Linux）
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNDIR="$ROOT/backend/run"

for name in web scheduler; do
  PIDF="$RUNDIR/$name.pid"
  if [ -f "$PIDF" ]; then
    PID="$(cat "$PIDF")"
    if kill "$PID" 2>/dev/null; then
      echo "已停止 $name (pid $PID)"
    fi
    rm -f "$PIDF"
  fi
done
