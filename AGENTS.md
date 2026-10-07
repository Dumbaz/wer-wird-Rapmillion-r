# AGENTS.md

Guidance for AI coding agents (and humans) working in this repository.
Read this first; [`README.md`](README.md) has the full user-facing documentation (German).

## What this is

"Wer wird Rapmillionär" — a *Who Wants to Be a Millionaire*-style quiz about
German rap lyrics. A verified lyric line is shown, the player picks the artist
out of three, and climbs a 15-step prize ladder (50 € → 1.000.000 €).

- `backend/` — Python FastAPI app. Owns all game state and answer checking.
- `frontend/` — React 18 + TypeScript + Vite SPA. Renders state from the API.
- No database: sessions are in memory (`SessionStore`, TTL 6 h).

**Language:** UI text, docstrings, comments, test names and commit messages are
German. Python source uses ASCII transliterations in comments/docstrings
(`ae`, `oe`, `ue`, `ss`); user-facing strings and catalog data use real
umlauts. Keep both conventions.

## Commands

All backend commands run from `backend/` with the venv active
(`source .venv/bin/activate`, or prefix with `.venv/bin/`).

| Task | Command |
|---|---|
| Start everything | `./start.sh` (prod, :8000) or `./start.sh --dev` (backend :8000 + Vite :5173); bootstraps venv/node_modules |
| Install backend | `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` |
| Run backend | `uvicorn app.main:app --reload` (port 8000) |
| Backend tests | `python -m pytest tests -q` (22 tests, < 2 s) |
| Verify quotes | `python tools/verify_sources.py [q001 …]` (needs network, hits genius.com) |
| Regenerate covers | `python tools/gen_covers.py` |
| Install frontend | `cd frontend && npm install` |
| Run frontend | `npm run dev` (port 5173, proxies `/api` and `/covers` to :8000) |
| Typecheck | `npm run typecheck` |
| Build | `npm run build` → `frontend/dist/`, served by FastAPI at `/` if present |
| Visual smoke test | build, run backend on `:8014`, then `npm run shots` (Playwright, screenshots to `/tmp/shots`) |

Before finishing a change: run `pytest` for backend changes, `npm run typecheck`
for frontend changes, and both if you touched the API contract.

## Map

```
backend/app/main.py            app setup, CORS (localhost:5173), mounts /covers and dist/
backend/app/routes.py          /api/game endpoints; GameError -> 409, unknown session -> 404
backend/app/game.py            PRIZES, SAFE_HAVENS, Session (draw/shuffle/answer/lifelines/cashout), SessionStore
backend/app/models.py          Pydantic models — the API contract
backend/app/data/questions.py  RAW question catalog -> QUESTIONS, QUESTIONS_BY_LEVEL
backend/tools/                 gen_covers.py, verify_sources.py
backend/tests/test_api.py      catalog quality + API end-to-end tests
backend/static/covers/         generated SVG covers ONLY (committed)
frontend/src/App.tsx           game state machine, localStorage resume offer
frontend/src/api.ts, types.ts  fetch client + TS mirror of models.py
frontend/src/audio/sfx.ts      synthesized Web Audio effects (no audio files)
frontend/src/components/       StartScreen, Ladder, AnswerButton, Lifelines, CoverReveal, GameOver
```

## Invariants — do not break

1. **The correct answer never leaves the server before `/answer`.** Clients get
   `PublicQuestion` (no `correct_index`, no artist/track). Answers are shuffled
   per session (`shuffle_by_level`); indexes in requests/responses are *display*
   indexes. A test asserts this.
2. **Every catalog line must be quoted verbatim from its Genius `source` URL.**
   Never write, "fix", or paraphrase a lyric from memory. An earlier catalog
   contained invented lines; that's why `verify_sources.py` and the
   source-required test exist. If you can't verify a line, don't add it.
3. **Every level has the same number of questions** (currently 9 × 15 = 135).
   Tests enforce equal counts and ≥ 3 per level.
4. **Catalog entry rules** (enforced by tests): exactly 3 unique answers;
   `answers[correct] == artist`; artist name (tokens ≥ 4 chars) must not appear
   in the line; no duplicate lines or songs; `source` is `https://genius.com/…-lyrics`.
5. **Content filter:** crude/vulgar lines are fine (genre), but exclude homophobic
   slurs, xenophobic/racist terms, Nazi comparisons and ableist insults — checked
   against the *whole song*, not just the quoted line. This is a manual check;
   there is no script for it.
6. **Covers are generated SVGs only.** Don't add real album artwork (copyright;
   see README "Rechtliches"). `static/covers/` must contain only covers.
   Filenames derive from `_slug(artist)--_slug(album).svg`; the generator
   overwrites and prunes orphans.
7. **Backend and frontend types must match.** Change `models.py` and
   `frontend/src/types.ts` together.

## Gotchas

- Question IDs (`q001` …) are assigned by position in `RAW`. Inserting mid-list
  renumbers everything after it — append when possible.
- After any catalog change: `gen_covers.py` → `verify_sources.py` → `pytest`.
  `test_alle_cover_dateien_existieren` fails if you skip the generator.
- Sessions die on backend restart; the frontend then drops its stored session ID.
- Saved sessions are *offered* on the start screen, not auto-resumed (deliberate,
  see commit `e418b1e`). Don't reintroduce auto-resume.
- Lifeline names are German-ish: `fifty_fifty`, `publikum`, `skip`.
- Safe havens: levels 5, 10 (and 15). Losing pays the highest cleared safe haven;
  cash-out pays the prize of the last cleared level.
- Test dependency is `httpx2` (required by the installed Starlette `TestClient`),
  not `httpx`.
- `*.tsbuildinfo` (TypeScript build cache), `backend/.venv` and `frontend/node_modules` are gitignored.
