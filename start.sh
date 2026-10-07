#!/usr/bin/env bash
# Startet das Spiel (rein statische Seite, kein Server-Backend noetig).
#
#   ./start.sh          Baut die Seite und zeigt sie unter http://127.0.0.1:4173
#   ./start.sh --dev    Entwicklungsmodus: Vite mit Hot Reload auf :5173
#
# Beim ersten Lauf werden venv, Python- und npm-Abhaengigkeiten automatisch
# installiert. Der Fragenkatalog (Python) wird bei jedem Start nach
# frontend/public/questions.json exportiert. Port: PORT=9000 ./start.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PORT="${PORT:-4173}"
MODE="prod"

case "${1:-}" in
  "") ;;
  --dev) MODE="dev" ;;
  -h|--help) sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "Unbekannte Option: $1 (siehe --help)" >&2; exit 1 ;;
esac

need() { command -v "$1" >/dev/null 2>&1 || { echo "Fehlt: $1 (bitte installieren)" >&2; exit 1; }; }
need python3
need node
need npm

# ------------------------------------------------------------------ Katalog
if [ ! -x "$BACKEND/.venv/bin/python" ]; then
  echo "==> Erstelle Python-venv"
  python3 -m venv "$BACKEND/.venv"
fi
PY="$BACKEND/.venv/bin/python"

# Requirements nur neu installieren, wenn sie sich geaendert haben
REQ_STAMP="$BACKEND/.venv/.requirements.stamp"
if [ ! -f "$REQ_STAMP" ] || [ "$BACKEND/requirements.txt" -nt "$REQ_STAMP" ]; then
  echo "==> Installiere Python-Abhaengigkeiten"
  "$PY" -m pip install --quiet -r "$BACKEND/requirements.txt"
  touch "$REQ_STAMP"
fi

# Cover fehlen? Dann generieren.
if [ -z "$(ls -A "$BACKEND/static/covers" 2>/dev/null)" ]; then
  echo "==> Generiere Albumcover"
  (cd "$BACKEND" && "$PY" tools/gen_covers.py)
fi

echo "==> Exportiere Fragenkatalog"
(cd "$BACKEND" && "$PY" tools/export_catalog.py)

# ----------------------------------------------------------------- Frontend
if [ ! -d "$FRONTEND/node_modules" ] || [ "$FRONTEND/package-lock.json" -nt "$FRONTEND/node_modules" ]; then
  echo "==> Installiere Frontend-Abhaengigkeiten"
  (cd "$FRONTEND" && npm install --no-audit --no-fund)
fi

# -------------------------------------------------------------------- Start
cd "$FRONTEND"
if [ "$MODE" = "dev" ]; then
  echo "==> Entwicklungsmodus: http://localhost:5173"
  exec npm run dev
else
  echo "==> Baue Frontend"
  npm run build
  echo "==> Spiel laeuft auf http://127.0.0.1:$PORT  (Strg+C beendet)"
  exec npx vite preview --host 127.0.0.1 --port "$PORT" --strictPort
fi
