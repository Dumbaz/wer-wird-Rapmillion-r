"""Prueft, ob jede Quiz-Zeile woertlich auf ihrer Genius-Quellseite steht.

Hintergrund: Ein frueherer Katalog enthielt frei erfundene Zeilen. Dieses
Skript ist die Gegenmassnahme - es faehrt den Katalog gegen die echten
Quellseiten und schlaegt fehl, sobald eine Zeile nicht belegbar ist.

Aufruf (aus dem Ordner backend/):
    python tools/verify_sources.py            # alle Eintraege
    python tools/verify_sources.py q003 q012  # nur bestimmte IDs

Exit-Code 0 = alles belegt, 1 = mindestens eine Zeile nicht auffindbar.
"""

from __future__ import annotations

import concurrent.futures as futures
import html
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.data.questions import QUESTIONS  # noqa: E402

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 30

# Typografische Varianten, die Genius uneinheitlich verwendet
EQUIVALENTS = {
    "\u2019": "'", "\u2018": "'", "\u201b": "'", "\u02bc": "'", "\u00b4": "'",
    "\u201e": '"', "\u201c": '"', "\u201d": '"', "\u00ab": '"', "\u00bb": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u00a0": " ", "\u200b": "", "\u2026": "...",
}


def strip_markup(raw_html: str) -> str:
    """HTML zu Klartext: Skripte raus, Tags raus, Entities aufloesen."""
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", raw_html, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for src, dst in EQUIVALENTS.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+", " ", text)
    return text.casefold().strip()


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, "ignore")


def verify(question) -> tuple[str, bool, str]:
    """Gibt (id, ok, detail) zurueck."""
    try:
        page = normalise(strip_markup(fetch(question.source_url)))
    except urllib.error.HTTPError as exc:
        return question.id, False, f"HTTP {exc.code} bei {question.source_url}"
    except Exception as exc:  # Netzwerkfehler, Timeout, ...
        return question.id, False, f"nicht abrufbar: {exc}"

    # Mehrzeilige Zitate sind mit " / " getrennt und werden einzeln geprueft
    for fragment in question.line.split(" / "):
        if normalise(fragment) not in page:
            return question.id, False, f"Zeile fehlt auf der Seite: {fragment!r}"
    return question.id, True, ""


def main(argv: list[str]) -> int:
    wanted = set(argv[1:])
    todo = [q for q in QUESTIONS if not wanted or q.id in wanted]
    if not todo:
        print("Keine passenden Eintraege.")
        return 1

    print(f"Pruefe {len(todo)} Zeilen gegen ihre Genius-Quellen ...\n")
    with futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(verify, todo))

    failed = [r for r in results if not r[1]]
    by_id = {q.id: q for q in todo}
    for qid, ok, detail in results:
        if not ok:
            q = by_id[qid]
            print(f"  FEHLT  {qid}  {q.artist} - {q.track}")
            print(f"         {detail}")
            print(f"         {q.source_url}")

    print(f"\nBelegt: {len(results) - len(failed)}/{len(results)}")
    if failed:
        print("Nicht belegte Zeilen gehoeren nicht in den Katalog.")
        return 1
    print("Alle Zeilen sind woertlich auf der angegebenen Quelle nachweisbar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
