"""Tests fuer die Qualitaet des Fragenkatalogs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.questions import QUESTIONS, QUESTIONS_BY_LEVEL  # noqa: E402

MAX_LEVEL = 15


# --------------------------------------------------------------- Datenqualitaet
def test_katalog_hat_genug_fragen_pro_level():
    """Jede Stufe braucht mehrere Fragen, damit Runden sich unterscheiden.

    Die Stufen muessen nicht gleich gross sein: der Katalog waechst jahrgangs-
    weise, und nicht jedes Jahr gibt in jeder Schwierigkeit etwas her.
    """
    assert len(QUESTIONS) >= 45
    for level in range(1, MAX_LEVEL + 1):
        assert len(QUESTIONS_BY_LEVEL[level]) >= 9, f"Level {level}"


def test_jede_frage_hat_drei_eindeutige_antworten():
    for q in QUESTIONS:
        assert len(q.answers) == 3
        assert len(set(q.answers)) == 3, q.id
        assert q.answers[q.correct_index] == q.artist, q.id


def test_jede_zeile_hat_eine_belegquelle():
    """Quellenpflicht: ohne verifizierbare Lyrics-Quelle kein Eintrag.

    Dieser Test existiert, weil ein frueherer Katalog erfundene Zeilen enthielt.
    """
    for q in QUESTIONS:
        assert q.source_url.startswith("https://"), q.id
        assert "genius.com" in q.source_url, q.id
        assert q.source_url.endswith("-lyrics"), q.id


def test_zeile_verraet_die_antwort_nicht():
    """Der Kuenstlername darf nicht in der Zeile stehen."""
    for q in QUESTIONS:
        haystack = q.line.casefold()
        for token in q.artist.replace("&", " ").split():
            token = token.strip(".").casefold()
            if len(token) < 4:
                continue
            assert token not in haystack, f"{q.id}: '{token}' steht in der Zeile"


def test_zeilen_sind_eindeutig_und_plausibel_lang():
    lines = [q.line for q in QUESTIONS]
    assert len(set(lines)) == len(lines), "doppelte Zeilen im Katalog"
    for q in QUESTIONS:
        assert 3 <= len(q.line.split()) <= 20, f"{q.id}: {len(q.line.split())} Woerter"


def test_quellen_sind_eindeutig_pro_song():
    """Kein Song darf zweimal als Frage vorkommen."""
    urls = [q.source_url for q in QUESTIONS]
    assert len(set(urls)) == len(urls), "derselbe Song mehrfach im Katalog"


def test_alle_cover_dateien_existieren():
    covers = Path(__file__).resolve().parent.parent / "static" / "covers"
    for q in QUESTIONS:
        assert (covers / q.cover).is_file(), q.cover


# ------------------------------------------- Keine Mehrdeutigkeit bei Gruppen
# Gruppe/Duo -> Mitglieder bzw. Alias. Zwei Antwortoptionen einer Frage duerfen
# keine gemeinsame Person enthalten (z. B. "187 Strassenbande" und "Gzuz"),
# sonst ist die Frage unfair mehrdeutig.
GROUP_MEMBERS: dict[str, set[str]] = {
    "187 strassenbande": {"gzuz", "bonez mc", "maxwell", "lx", "sa4"},
    "bonez mc & raf camora": {"bonez mc", "raf camora"},
    "berlins most wanted": {"bushido", "fler", "kay one", "bass sultan hengzt", "silla"},
    "aggro berlin": {"sido", "b-tight", "bushido", "fler"},
    "huss und hodn": {"retrogott", "hulk hodn"},
    "retrogott": {"retrogott"},
    "antilopen gang": {"koljah", "panik panzer", "danger dan"},
    "trailerpark": {"alligatoah", "timi hendrix", "sudden"},
    "mc bomber & mecstreem": {"mc bomber", "mecstreem"},
    "mc bomber": {"mc bomber"},
    "mecstreem": {"mecstreem"},
    "hiob": {"hiob"},
    "die fantastischen vier": {"smudo", "michi beck", "and.ypsilon", "thomas d"},
    "tic tac toe": {"lee", "jazzy", "ricky"},
    "seeed": {"peter fox", "pierre baigorry", "demba nabe", "eased", "frank delle"},
    "fettes brot": {"bjoern beton", "koenig boris", "dokter renz"},
    "beginner": {"jan delay", "denyo", "dj mad"},
    "absolute beginner": {"jan delay", "denyo", "dj mad"},
    "roedelheim hartreim projekt": {"moses pelham", "thomas hofmann"},
    "rödelheim hartreim projekt": {"moses pelham", "thomas hofmann"},
    "dynamite deluxe": {"samy deluxe", "tropf", "dj dynamite"},
    "fünf sterne deluxe": {"das bo", "tobi tobsen", "dj coolmann"},
    "freundeskreis": {"max herre", "don philippe", "dj friction"},
    "k.i.z": {"tarek", "nico", "maxim", "dj craft"},
    "eins zwo": {"dendemann", "dj rabauke"},
    "deichkind": {"kryptik joe", "porky", "ferris mc"},
    "culcha candela": {"mr. reedoo", "johnny strange", "itchyban"},
    "morlockk dilemma": {"morlockk dilemma"},
}


def _people(option: str) -> set[str]:
    key = option.casefold()
    if key in GROUP_MEMBERS:
        return GROUP_MEMBERS[key] | {key}
    parts = {p.strip() for p in key.replace(" und ", " & ").split("&")}
    return parts | {key}


def test_antwortoptionen_ueberschneiden_sich_nicht_personell():
    for q in QUESTIONS:
        sets = [_people(a) for a in q.answers]
        for i in range(3):
            for j in range(i + 1, 3):
                shared = sets[i] & sets[j]
                assert not shared, (
                    f"{q.id}: '{q.answers[i]}' und '{q.answers[j]}' "
                    f"teilen {shared}"
                )
