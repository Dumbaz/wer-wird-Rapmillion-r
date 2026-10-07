"""End-to-End-Tests der Quiz-API."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.questions import QUESTIONS, QUESTIONS_BY_LEVEL  # noqa: E402
from app.game import MAX_LEVEL, PRIZES, SAFE_HAVENS, store  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def correct_index(session_id: str) -> int:
    """Loest die richtige Antwort aus dem Server-State (nur fuer Tests)."""
    session = store.get(session_id)
    return session.display_correct_index(session.level)


def new_game() -> dict:
    response = client.post("/api/game")
    assert response.status_code == 201
    return response.json()


# --------------------------------------------------------------- Datenqualitaet
def test_katalog_hat_genug_fragen_pro_level():
    """Jede Stufe braucht mehrere Fragen, damit Runden sich unterscheiden."""
    assert len(QUESTIONS) >= 45
    for level in range(1, MAX_LEVEL + 1):
        assert len(QUESTIONS_BY_LEVEL[level]) >= 3, f"Level {level}"

    counts = {len(v) for v in QUESTIONS_BY_LEVEL.values()}
    assert len(counts) == 1, f"Stufen ungleich gefuellt: {counts}"


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


def test_gewinnleiter_steigt_monoton():
    prizes = [PRIZES[lvl] for lvl in range(1, MAX_LEVEL + 1)]
    assert prizes == sorted(prizes)
    assert prizes[-1] == 1_000_000


# ------------------------------------------------------------------- API-Basics
def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_start_liefert_frage_ohne_loesung():
    state = new_game()
    assert state["status"] == "running"
    assert state["level"] == 1
    assert state["banked"] == 0
    assert len(state["ladder"]) == MAX_LEVEL
    question = state["question"]
    assert len(question["answers"]) == 3
    assert "correct_index" not in question
    assert "artist" not in question


def test_unbekannte_session_gibt_404():
    assert client.get("/api/game/gibtsnicht").status_code == 404


# -------------------------------------------------------------- Spielverlauf
def test_kompletter_durchlauf_bis_zur_million():
    state = new_game()
    sid = state["session_id"]

    for level in range(1, MAX_LEVEL + 1):
        assert state["level"] == level
        result = client.post(
            f"/api/game/{sid}/answer", json={"answer_index": correct_index(sid)}
        ).json()
        assert result["correct"] is True
        assert result["prize_won"] == PRIZES[level]
        reveal = result["reveal"]
        assert reveal["cover_url"].endswith(".svg")
        assert "/covers/" in reveal["cover_url"]
        assert reveal["artist"] and reveal["album"]
        assert "genius.com" in reveal["source_url"]
        state = result["state"]

    assert state["status"] == "won"
    assert state["banked"] == 1_000_000
    assert state["question"] is None


def test_falsche_antwort_beendet_spiel_und_deckt_cover_auf():
    state = new_game()
    sid = state["session_id"]
    wrong = (correct_index(sid) + 1) % 3

    result = client.post(f"/api/game/{sid}/answer", json={"answer_index": wrong}).json()
    assert result["correct"] is False
    assert result["correct_index"] != wrong
    assert result["reveal"]["cover_url"].endswith(".svg")
    assert result["state"]["status"] == "lost"
    assert result["state"]["banked"] == 0

    # Kein Weiterspielen nach dem Aus
    assert client.post(f"/api/game/{sid}/answer", json={"answer_index": 0}).status_code == 409


def test_sicherheitsstufe_sichert_gewinn():
    state = new_game()
    sid = state["session_id"]

    for _ in range(min(SAFE_HAVENS)):  # Level 1-5 richtig
        state = client.post(
            f"/api/game/{sid}/answer", json={"answer_index": correct_index(sid)}
        ).json()["state"]

    assert state["level"] == 6
    assert state["guaranteed"] == PRIZES[5]

    wrong = (correct_index(sid) + 1) % 3
    result = client.post(f"/api/game/{sid}/answer", json={"answer_index": wrong}).json()
    assert result["state"]["status"] == "lost"
    assert result["state"]["banked"] == PRIZES[5]


def test_cashout_sichert_bisherigen_gewinn():
    state = new_game()
    sid = state["session_id"]
    for _ in range(3):
        state = client.post(
            f"/api/game/{sid}/answer", json={"answer_index": correct_index(sid)}
        ).json()["state"]

    final = client.post(f"/api/game/{sid}/cashout").json()
    assert final["status"] == "cashed_out"
    assert final["banked"] == PRIZES[3]


# ------------------------------------------------------------------- Joker
def test_fifty_fifty_entfernt_genau_eine_falsche_antwort():
    sid = new_game()["session_id"]
    correct = correct_index(sid)
    result = client.post(
        f"/api/game/{sid}/lifeline", json={"lifeline": "fifty_fifty"}
    ).json()

    assert len(result["removed_indexes"]) == 1
    assert result["removed_indexes"][0] != correct
    assert result["state"]["lifelines"]["fifty_fifty"] is False

    # Nur einmal nutzbar
    assert (
        client.post(f"/api/game/{sid}/lifeline", json={"lifeline": "fifty_fifty"}).status_code
        == 409
    )


def test_publikumsjoker_ergibt_hundert_prozent():
    sid = new_game()["session_id"]
    correct = correct_index(sid)
    votes = client.post(
        f"/api/game/{sid}/lifeline", json={"lifeline": "publikum"}
    ).json()["audience_votes"]

    assert len(votes) == 3
    assert sum(votes) == 100
    assert votes[correct] == max(votes)


def test_skip_zieht_neue_frage():
    state = new_game()
    sid = state["session_id"]
    before = state["question"]["id"]

    result = client.post(f"/api/game/{sid}/lifeline", json={"lifeline": "skip"}).json()
    assert result["state"]["question"]["id"] != before
    assert result["state"]["level"] == 1
    assert result["state"]["lifelines"]["skip"] is False


@pytest.mark.parametrize("lifeline", ["fifty_fifty", "publikum", "skip"])
def test_joker_nach_spielende_abgelehnt(lifeline: str):
    sid = new_game()["session_id"]
    wrong = (correct_index(sid) + 1) % 3
    client.post(f"/api/game/{sid}/answer", json={"answer_index": wrong})
    assert (
        client.post(f"/api/game/{sid}/lifeline", json={"lifeline": lifeline}).status_code == 409
    )


def test_antworten_werden_gemischt():
    """Ueber viele Sessions darf die Loesung nicht immer an Position 0 stehen."""
    positions = set()
    for _ in range(30):
        sid = new_game()["session_id"]
        positions.add(correct_index(sid))
    assert len(positions) > 1


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
