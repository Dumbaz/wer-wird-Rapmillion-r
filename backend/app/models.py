"""Pydantic-Modelle fuer das Deutschrap-Quiz."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Lifeline = Literal["fifty_fifty", "publikum", "skip"]


class Question(BaseModel):
    """Interne Repraesentation einer Frage (enthaelt die Loesung)."""

    id: str
    level: int = Field(ge=1, le=15)
    line: str
    answers: list[str] = Field(min_length=3, max_length=3)
    correct_index: int = Field(ge=0, le=2)
    artist: str
    track: str
    album: str
    year: int
    cover: str
    fun_fact: str


class PublicQuestion(BaseModel):
    """Frage, wie sie an den Client geht - ohne Loesung."""

    id: str
    level: int
    line: str
    answers: list[str]
    prize: int
    safe_haven: bool


class LadderStep(BaseModel):
    level: int
    prize: int
    safe_haven: bool


class SongReveal(BaseModel):
    """Metadaten, die nach der Antwort aufgedeckt werden."""

    artist: str
    track: str
    album: str
    year: int
    cover_url: str
    fun_fact: str


class LifelineState(BaseModel):
    fifty_fifty: bool = True
    publikum: bool = True
    skip: bool = True


class GameState(BaseModel):
    """Vollstaendiger, an den Client ausgelieferter Spielzustand."""

    session_id: str
    status: Literal["running", "lost", "won", "cashed_out"]
    level: int
    banked: int
    guaranteed: int
    lifelines: LifelineState
    ladder: list[LadderStep]
    question: PublicQuestion | None = None


class AnswerRequest(BaseModel):
    answer_index: int = Field(ge=0, le=2)


class AnswerResult(BaseModel):
    correct: bool
    correct_index: int
    reveal: SongReveal
    prize_won: int
    state: GameState


class LifelineRequest(BaseModel):
    lifeline: Lifeline


class LifelineResult(BaseModel):
    lifeline: Lifeline
    removed_indexes: list[int] = []
    audience_votes: list[int] = []
    state: GameState
