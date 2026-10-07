"""Pydantic-Modelle fuer das Deutschrap-Quiz."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
    source_url: str
