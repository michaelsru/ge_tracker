#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/venv"
FRONTEND="$ROOT/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173
URL="http://localhost:$FRONTEND_PORT"

# ── colours ────────────────────────────────────────────────
GREEN='\033[0;32m'; CYAN='\033[0;36m'; GRAY='\033[0;90m'; RESET='\033[0m'
log()  { echo -e "${CYAN}[ge-tracker]${RESET} $*"; }
ok()   { echo -e "${GREEN}[ge-tracker]${RESET} $*"; }
dim()  { echo -e "${GRAY}$*${RESET}"; }

# ── cleanup on exit ─────────────────────────────────────────
PIDS=()
cleanup() {
  echo ""
  log "Shutting down..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null
  ok "Done."
}
trap cleanup INT TERM EXIT

# ── backend ─────────────────────────────────────────────────
log "Starting backend (port $BACKEND_PORT)..."
source "$VENV/bin/activate"
uvicorn backend.main:app --port "$BACKEND_PORT" --reload \
  --log-level warning \
  2>&1 | sed "s/^/$(dim '[backend] ')/" &
PIDS+=($!)

# Wait until backend is accepting connections
for i in $(seq 1 20); do
  if curl -sf "http://localhost:$BACKEND_PORT/api/prices" -o /dev/null 2>/dev/null; then break; fi
  sleep 0.5
done

# ── frontend ────────────────────────────────────────────────
log "Starting frontend (port $FRONTEND_PORT)..."
cd "$FRONTEND"
npm run dev -- --port "$FRONTEND_PORT" 2>&1 | sed "s/^/$(dim '[frontend] ')/" &
PIDS+=($!)
cd "$ROOT"

# Wait for Vite to be ready
for i in $(seq 1 20); do
  if curl -sf "$URL" -o /dev/null 2>/dev/null; then break; fi
  sleep 0.5
done

# ── open browser ────────────────────────────────────────────
ok "Dashboard ready → $URL"
open "$URL"

log "Press Ctrl+C to stop"
wait
