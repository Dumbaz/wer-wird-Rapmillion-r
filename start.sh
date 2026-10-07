#!/usr/bin/env bash
# Startet das komplette Spiel: Backend + Frontend.
#
#   ./start.sh          Produktionsmodus: baut das Frontend, ein Prozess auf :8000
#   ./start.sh --dev    Entwicklungsmodus: uvicorn --reload (:8000) + Vite (:5173)
#
# Beim ersten Lauf werden venv, Python- und npm-Abhaengigkeiten automatisch
# installiert. Port ueberschreiben: PORT=9000 ./start.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PORT="${PORT:-8000}"
MODE="prod"

case "${1:-}" in
  "") ;;
  --dev) MODE="dev" ;;
  -h|--help) sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "Unbekannte Option: $1 (siehe --help)" >&2; exit 1 ;;
esac

need() { command -v "$1" >/dev/null 2>&1 || { echo "Fehlt: $1 (bitte installieren)" >&2; exit 1; }; }
need python3
need node
need npm

# ------------------------------------------------------------------ Backend
if [ ! -x "$BACKEND/.venv/bin/python" ]; then
  echo "==> Erstelle Python-venv"
  python3 -m venv "$BACKEND/.venv"
fi
PY="$BACKEND/.venv/bin/python"

# Requirements nur neu installieren, wenn sie sich geaendert haben
REQ_STAMP="$BACKEND/.venv/.requirements.stamp"
if [ ! -f "$REQ_STAMP" ] || [ "$BACKEND/requirements.txt" -nt "$REQ_STAMP" ]; then
  echo "==> Installiere Backend-Abhaengigkeiten"
  "$PY" -m pip install --quiet -r "$BACKEND/requirements.txt"
  touch "$REQ_STAMP"
fi

# Cover fehlen? Dann generieren.
if [ -z "$(ls -A "$BACKEND/static/covers" 2>/dev/null)" ]; then
  echo "==> Generiere Albumcover"
  (cd "$BACKEND" && "$PY" tools/gen_covers.py)
fi

# ----------------------------------------------------------------- Frontend
if [ ! -d "$FRONTEND/node_modules" ] || [ "$FRONTEND/package-lock.json" -nt "$FRONTEND/node_modules" ]; then
  echo "==> Installiere Frontend-Abhaengigkeiten"
  (cd "$FRONTEND" && npm install --no-audit --no-fund)
fi

# -------------------------------------------------------------------- Start
if [ "$MODE" = "dev" ]; then
  echo "==> Entwicklungsmodus: Backend :8000, Frontend http://localhost:5173"
  (cd "$BACKEND" && exec "$PY" -m uvicorn app.main:app --reload --port 8000) &
  BACKEND_PID=$!
  trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT INT TERM
  cd "$FRONTEND" && npm run dev
else
  # Neu bauen, wenn dist fehlt oder Quellen neuer sind
  if [ ! -d "$FRONTEND/dist" ] || [ -n "$(find "$FRONTEND/src" "$FRONTEND/index.html" "$FRONTEND/package.json" -newer "$FRONTEND/dist" -print -quit)" ]; then
    echo "==> Baue Frontend"
    (cd "$FRONTEND" && npm run build)
  fi
  echo "==> Spiel laeuft auf http://127.0.0.1:$PORT  (Strg+C beendet)"
  cd "$BACKEND" && exec "$PY" -m uvicorn app.main:app --port "$PORT"
fi
