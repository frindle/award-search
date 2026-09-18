#!/usr/bin/env bash
# Start the award-search web UI on the claude-sandbox box.
# Nothing in this project runs on Penn's primary Mac.
# Idempotent: stops any previous instance on the same port first.
set -euo pipefail

APP_DIR="$HOME/apps/award-search"
PORT="${AWARD_SEARCH_PORT:-8811}"

cd "$APP_DIR"
pkill -f "uvicorn src.webui.app:app .*--port ${PORT}" 2>/dev/null || true
sleep 1

nohup .venv/bin/python -m uvicorn src.webui.app:app \
      --host 0.0.0.0 --port "$PORT" \
      >> "$APP_DIR/webui.log" 2>&1 &

echo $! > "$APP_DIR/webui.pid"
sleep 4
echo "award-search web UI on 0.0.0.0:${PORT} (pid $(cat "$APP_DIR/webui.pid"))"
curl -s -o /dev/null -w "self-check / -> %{http_code}\n" "http://127.0.0.1:${PORT}/"
