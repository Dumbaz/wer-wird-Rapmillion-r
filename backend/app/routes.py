"""API-Routen des Quiz-Backends."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .game import GameError, store
from .models import (
    AnswerRequest,
    AnswerResult,
    GameState,
    LifelineRequest,
    LifelineResult,
)

router = APIRouter(prefix="/api", tags=["game"])

# Relativer Pfad: funktioniert sowohl hinter dem Vite-Proxy als auch,
# wenn das gebaute Frontend direkt von FastAPI ausgeliefert wird.
COVER_BASE = "/covers"


def _session(session_id: str):
    try:
        return store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session nicht gefunden") from None


@router.post("/game", response_model=GameState, status_code=201)
def start_game() -> GameState:
    """Startet eine neue Quizrunde."""
    return store.create().state()


@router.get("/game/{session_id}", response_model=GameState)
def get_game(session_id: str) -> GameState:
    """Liefert den aktuellen Spielzustand (reload-fest)."""
    return _session(session_id).state()


@router.post("/game/{session_id}/answer", response_model=AnswerResult)
def answer(session_id: str, payload: AnswerRequest) -> AnswerResult:
    """Prueft eine Antwort serverseitig und deckt den Song auf."""
    session = _session(session_id)
    try:
        correct, correct_index, reveal, prize = session.answer(
            payload.answer_index, COVER_BASE
        )
    except GameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return AnswerResult(
        correct=correct,
        correct_index=correct_index,
        reveal=reveal,
        prize_won=prize,
        state=session.state(),
    )


@router.post("/game/{session_id}/lifeline", response_model=LifelineResult)
def lifeline(session_id: str, payload: LifelineRequest) -> LifelineResult:
    """Setzt einen Joker ein (50:50, Publikum oder Skip)."""
    session = _session(session_id)
    try:
        removed, votes = session.use_lifeline(payload.lifeline)
    except GameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return LifelineResult(
        lifeline=payload.lifeline,
        removed_indexes=removed,
        audience_votes=votes,
        state=session.state(),
    )


@router.post("/game/{session_id}/cashout", response_model=GameState)
def cashout(session_id: str) -> GameState:
    """Steigt aus und sichert das bisher erspielte Geld."""
    session = _session(session_id)
    try:
        session.cash_out()
    except GameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return session.state()
