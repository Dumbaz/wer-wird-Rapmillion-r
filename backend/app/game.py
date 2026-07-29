"""Spiellogik: Gewinnleiter, Sessions, Joker."""

from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass, field

from .data.questions import QUESTIONS_BY_LEVEL
from .models import (
    GameState,
    LadderStep,
    LifelineState,
    PublicQuestion,
    Question,
    SongReveal,
)

MAX_LEVEL = 15
SESSION_TTL_SECONDS = 60 * 60 * 6

# Gewinnleiter: Level -> Preisgeld in Euro
PRIZES: dict[int, int] = {
    1: 50,
    2: 100,
    3: 200,
    4: 300,
    5: 500,
    6: 1_000,
    7: 2_000,
    8: 4_000,
    9: 8_000,
    10: 16_000,
    11: 32_000,
    12: 64_000,
    13: 125_000,
    14: 500_000,
    15: 1_000_000,
}

SAFE_HAVENS: frozenset[int] = frozenset({5, 10, 15})

LADDER: list[LadderStep] = [
    LadderStep(level=lvl, prize=PRIZES[lvl], safe_haven=lvl in SAFE_HAVENS)
    for lvl in range(1, MAX_LEVEL + 1)
]


def guaranteed_prize(cleared_level: int) -> int:
    """Hoechster erreichter Sicherheitsbetrag nach `cleared_level` Stufen."""
    best = 0
    for lvl in sorted(SAFE_HAVENS):
        if lvl <= cleared_level:
            best = PRIZES[lvl]
    return best


class GameError(Exception):
    """Fachlicher Fehler in der Spiellogik."""


@dataclass
class Session:
    id: str
    created_at: float
    level: int = 1
    status: str = "running"
    banked: int = 0
    lifelines: LifelineState = field(default_factory=LifelineState)
    # Reihenfolge der gezogenen Fragen pro Level
    question_by_level: dict[int, Question] = field(default_factory=dict)
    # Pro Frage gemischte Antwortreihenfolge: Liste von Original-Indizes
    shuffle_by_level: dict[int, list[int]] = field(default_factory=dict)
    used_question_ids: set[str] = field(default_factory=set)
    removed_by_level: dict[int, list[int]] = field(default_factory=dict)

    # -------------------------------------------------------------- Fragen
    def current_question(self) -> Question | None:
        if self.status != "running" or self.level > MAX_LEVEL:
            return None
        if self.level not in self.question_by_level:
            self._draw(self.level)
        return self.question_by_level[self.level]

    def _draw(self, level: int) -> None:
        pool = [
            q for q in QUESTIONS_BY_LEVEL.get(level, [])
            if q.id not in self.used_question_ids
        ]
        if not pool:
            pool = QUESTIONS_BY_LEVEL.get(level, [])
        if not pool:
            raise GameError(f"Keine Fragen fuer Level {level} hinterlegt")
        question = random.choice(pool)
        self.used_question_ids.add(question.id)
        self.question_by_level[level] = question
        order = list(range(len(question.answers)))
        random.shuffle(order)
        self.shuffle_by_level[level] = order

    def display_answers(self, level: int) -> list[str]:
        question = self.question_by_level[level]
        order = self.shuffle_by_level[level]
        return [question.answers[i] for i in order]

    def display_correct_index(self, level: int) -> int:
        question = self.question_by_level[level]
        return self.shuffle_by_level[level].index(question.correct_index)

    # ---------------------------------------------------------------- View
    def public_question(self) -> PublicQuestion | None:
        question = self.current_question()
        if question is None:
            return None
        return PublicQuestion(
            id=question.id,
            level=question.level,
            line=question.line,
            answers=self.display_answers(question.level),
            prize=PRIZES[question.level],
            safe_haven=question.level in SAFE_HAVENS,
        )

    def state(self) -> GameState:
        return GameState(
            session_id=self.id,
            status=self.status,  # type: ignore[arg-type]
            level=min(self.level, MAX_LEVEL),
            banked=self.banked,
            guaranteed=guaranteed_prize(self.level - 1),
            lifelines=self.lifelines,
            ladder=LADDER,
            question=self.public_question(),
        )

    # --------------------------------------------------------------- Aktionen
    def answer(self, index: int, cover_base: str) -> tuple[bool, int, SongReveal, int]:
        if self.status != "running":
            raise GameError("Das Spiel ist bereits beendet")
        question = self.current_question()
        if question is None:
            raise GameError("Keine aktive Frage")

        correct_display_index = self.display_correct_index(self.level)
        correct = index == correct_display_index

        reveal = SongReveal(
            artist=question.artist,
            track=question.track,
            album=question.album,
            year=question.year,
            cover_url=f"{cover_base}/{question.cover}",
            source_url=question.source_url,
        )

        if correct:
            prize_won = PRIZES[self.level]
            if self.level == MAX_LEVEL:
                self.status = "won"
                self.banked = PRIZES[MAX_LEVEL]
                self.level = MAX_LEVEL
            else:
                self.banked = prize_won
                self.level += 1
        else:
            prize_won = guaranteed_prize(self.level - 1)
            self.status = "lost"
            self.banked = prize_won

        return correct, correct_display_index, reveal, prize_won

    def use_lifeline(self, lifeline: str) -> tuple[list[int], list[int]]:
        if self.status != "running":
            raise GameError("Das Spiel ist bereits beendet")
        if not getattr(self.lifelines, lifeline, False):
            raise GameError(f"Joker '{lifeline}' wurde bereits verbraucht")
        question = self.current_question()
        if question is None:
            raise GameError("Keine aktive Frage")

        correct = self.display_correct_index(self.level)
        wrong = [i for i in range(3) if i != correct]
        removed: list[int] = []
        votes: list[int] = []

        if lifeline == "fifty_fifty":
            removed = [random.choice(wrong)]
            self.removed_by_level.setdefault(self.level, []).extend(removed)
        elif lifeline == "publikum":
            votes = _audience_votes(correct, self.level)
        elif lifeline == "skip":
            # Frage ueberspringen: neue Frage auf gleichem Level ziehen
            self.question_by_level.pop(self.level, None)
            self.shuffle_by_level.pop(self.level, None)
            self.removed_by_level.pop(self.level, None)
            self._draw(self.level)
        else:
            raise GameError(f"Unbekannter Joker: {lifeline}")

        setattr(self.lifelines, lifeline, False)
        return removed, votes

    def cash_out(self) -> int:
        if self.status != "running":
            raise GameError("Das Spiel ist bereits beendet")
        self.status = "cashed_out"
        self.banked = PRIZES[self.level - 1] if self.level > 1 else 0
        return self.banked


def _audience_votes(correct_index: int, level: int) -> list[int]:
    """Plausible Publikumsverteilung - je hoeher das Level, desto unsicherer."""
    confidence = max(0.34, 0.92 - (level - 1) * 0.045)
    correct_share = random.uniform(confidence - 0.08, confidence + 0.05)
    correct_share = min(0.95, max(0.30, correct_share))

    rest = 1.0 - correct_share
    split = random.uniform(0.3, 0.7)
    shares = [0.0, 0.0, 0.0]
    others = [i for i in range(3) if i != correct_index]
    shares[correct_index] = correct_share
    shares[others[0]] = rest * split
    shares[others[1]] = rest * (1 - split)

    votes = [int(round(s * 100)) for s in shares]
    votes[correct_index] += 100 - sum(votes)
    return votes


class SessionStore:
    """In-Memory-Store mit TTL. Bewusst hinter einem Interface gekapselt,
    damit spaeter Redis/SQLite ohne Aenderung der Routen nutzbar ist."""

    def __init__(self, ttl: int = SESSION_TTL_SECONDS) -> None:
        self._sessions: dict[str, Session] = {}
        self._ttl = ttl

    def create(self) -> Session:
        self._evict()
        session = Session(id=uuid.uuid4().hex, created_at=time.time())
        session.current_question()
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session:
        self._evict()
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def _evict(self) -> None:
        cutoff = time.time() - self._ttl
        stale = [k for k, v in self._sessions.items() if v.created_at < cutoff]
        for key in stale:
            self._sessions.pop(key, None)


store = SessionStore()
