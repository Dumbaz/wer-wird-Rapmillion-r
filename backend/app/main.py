"""FastAPI-Anwendung: Deutschrap-Quiz Backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import router

BASE_DIR = Path(__file__).resolve().parent.parent
COVERS_DIR = BASE_DIR / "static" / "covers"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

app = FastAPI(
    title="Deutschrap-Quiz API",
    description="Backend fuer das 'Wer wird Rapmillionaer' Quiz.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# Albumcover liegen ausschliesslich in backend/static/covers/
COVERS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/covers", StaticFiles(directory=COVERS_DIR), name="covers")

# Optional: gebautes Frontend mit ausliefern (npm run build)
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
