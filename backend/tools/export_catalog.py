"""Exportiert den Fragenkatalog fuer das statische Frontend.

Schreibt frontend/public/questions.json und kopiert die Cover nach
frontend/public/covers/. Beides sind Build-Artefakte (nicht eingecheckt).

Aufruf (aus dem Ordner backend/):  python tools/export_catalog.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.data.questions import QUESTIONS  # noqa: E402

PUBLIC_DIR = BACKEND_DIR.parent / "frontend" / "public"
COVERS_SRC = BACKEND_DIR / "static" / "covers"
COVERS_DST = PUBLIC_DIR / "covers"


def main() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    missing = [q.id for q in QUESTIONS if not (COVERS_SRC / q.cover).is_file()]
    if missing:
        raise SystemExit(f"Cover fehlen fuer: {', '.join(missing)} (gen_covers.py laufen lassen)")

    data = [q.model_dump() for q in QUESTIONS]
    (PUBLIC_DIR / "questions.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    if COVERS_DST.exists():
        shutil.rmtree(COVERS_DST)
    shutil.copytree(COVERS_SRC, COVERS_DST)
    print(f"{len(data)} Fragen und {len(list(COVERS_DST.iterdir()))} Cover exportiert -> {PUBLIC_DIR}")


if __name__ == "__main__":
    main()
