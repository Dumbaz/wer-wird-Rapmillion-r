# AGENTS.md

Guidance for AI coding agents (and humans) working in this repository.
Read this first; [`README.md`](README.md) has the full user-facing documentation (German).

## What this is

"Wer wird Rapmillionär" — a *Who Wants to Be a Millionaire*-style quiz about
German rap lyrics. A verified lyric line is shown, the player picks the artist
out of three, and climbs a 15-step prize ladder (50 € → 1.000.000 €).

- `backend/` — Python: owns the question catalog (`app/data/questions.py`) and its tools/tests. No server.
- `frontend/` — React 18 + TypeScript + Vite static SPA. All game logic runs in the browser (`src/game.ts`).
- Published as a static site on GitHub Pages (`.github/workflows/pages.yml`). No database; the running round lives in `localStorage`.
- Correct answers ship in `questions.json` (accepted decision: casual quiz, no obfuscation).

**Language:** UI text, docstrings, comments, test names and commit messages are
German. Python source uses ASCII transliterations in comments/docstrings
(`ae`, `oe`, `ue`, `ss`); user-facing strings and catalog data use real
umlauts. Keep both conventions.

## Commands

Backend commands run from `backend/` with the venv active
(`source .venv/bin/activate`, or prefix with `.venv/bin/`).

| Task | Command |
|---|---|
| Start everything | `./start.sh` (export + build + preview, :4173) or `./start.sh --dev` (Vite :5173); bootstraps venv/node_modules |
| Install backend | `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` |
| Export catalog | `python tools/export_catalog.py` → `frontend/public/questions.json` + `covers/` (gitignored build artifacts) |
| Catalog tests | `python -m pytest tests -q` (< 2 s) |
| Verify quotes | `python tools/verify_sources.py [q001 …]` (needs network, hits genius.com) |
| Regenerate covers | `python tools/gen_covers.py` |
| Install frontend | `cd frontend && npm install` |
| Run frontend | `npm run dev` (port 5173; needs the export first) |
| Typecheck / tests | `npm run typecheck`, `npm test` (Vitest) |
| Build | `npm run build` → `frontend/dist/` (base `./`) |
| Visual smoke test | `./start.sh`, then `npm run shots` (Playwright, screenshots to `/tmp/shots`) |

Before finishing a change: `pytest` for catalog changes, `npm run typecheck` and
`npm test` for frontend changes. Pushing to `main` deploys via GitHub Actions
(one-time setting: Settings → Pages → Source: GitHub Actions).

## Map

```
backend/app/models.py          Pydantic Question model (the catalog/JSON contract)
backend/app/data/questions.py  RAW question catalog -> QUESTIONS, QUESTIONS_BY_LEVEL
backend/tools/                 export_catalog.py, gen_covers.py, verify_sources.py
backend/tests/test_catalog.py  catalog quality tests
backend/static/covers/         generated SVG covers ONLY (committed; copied to frontend/public by the export)
frontend/src/game.ts           PRIZES, SAFE_HAVENS, Game (draw/shuffle/answer/lifelines/cashout), serializable Session
frontend/src/game.test.ts      Vitest tests of the game logic
frontend/src/api.ts, types.ts  local "API" over game.ts + localStorage; TS types
frontend/src/App.tsx           game state machine, localStorage resume offer
frontend/src/audio/sfx.ts      synthesized Web Audio effects (no audio files)
frontend/src/components/       StartScreen, Ladder, AnswerButton, Lifelines, CoverReveal, GameOver
```

## Invariants — do not break

1. **The UI never shows the solution before the player answers.** The shipped
   JSON contains it (accepted), but `Game.state()` only exposes the public
   question (no `correct_index`, no artist/track). Answers are shuffled per
   round (`shuffleByLevel`); indexes passed to/returned from `Game` are *display*
   indexes. A Vitest test asserts the public state has no `correct_index`.
2. **Every catalog line must be quoted verbatim from its Genius `source` URL.**
   Never write, "fix", or paraphrase a lyric from memory. An earlier catalog
   contained invented lines; that's why `verify_sources.py` and the
   source-required test exist. If you can't verify a line, don't add it.
3. **Every level needs at least 9 questions** (test-enforced in `test_catalog.py`). Levels may differ
   in size; the catalog grows year by year.
4. **Catalog entry rules** (enforced by tests): exactly 3 unique answers;
   `answers[correct] == artist`; artist name (tokens ≥ 4 chars) must not appear
   in the line; no duplicate lines or songs; no two answer options share a person
   (group + member, e.g. `187 Strassenbande` vs `Gzuz`; extend `GROUP_MEMBERS` in the test); `source` is `https://genius.com/…-lyrics`.
5. **Content filter:** crude/vulgar lines are fine (genre), but exclude homophobic
   slurs, xenophobic/racist terms, Nazi comparisons and ableist insults — checked
   against the *whole song*, not just the quoted line. This is a manual check;
   there is no script for it.
6. **Covers are generated SVGs only.** Don't add real album artwork (copyright;
   see README "Rechtliches"). `static/covers/` must contain only covers.
   Filenames derive from `_slug(artist)--_slug(album).svg`; the generator
   overwrites and prunes orphans.
7. **Catalog schema and frontend types must match.** Change `models.py` and
   `Question` in `frontend/src/game.ts` together.

## Gotchas

- Question IDs (`q001` …) are assigned by position in `RAW`. Inserting mid-list
  renumbers everything after it — append when possible.
- After any catalog change: `gen_covers.py` → `verify_sources.py` → `pytest` → `export_catalog.py`.
  `test_alle_cover_dateien_existieren` fails if you skip the generator.
- A stored round that no longer matches (corrupt, other ID) is dropped by `api.ts`; the start screen then shows no resume offer.
- Saved sessions are *offered* on the start screen, not auto-resumed (deliberate,
  see commit `e418b1e`). Don't reintroduce auto-resume.
- Lifeline names are German-ish: `fifty_fifty`, `publikum`, `skip`.
- Safe havens: levels 5, 10 (and 15). Losing pays the highest cleared safe haven;
  cash-out pays the prize of the last cleared level.
- `*.tsbuildinfo` (TypeScript build cache), `backend/.venv`, `frontend/node_modules`, `frontend/public/questions.json` and `frontend/public/covers/` are gitignored.
