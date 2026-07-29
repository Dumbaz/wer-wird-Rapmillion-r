# Wer wird Rapmillionär – Deutschrap-Quiz

Ein Quiz im Stil von „Wer wird Millionär": Eine bekannte Line aus dem deutschen
Rap wird gezeigt, drei Antworten stehen zur Auswahl. Wer richtig liegt, steigt
die Gewinnleiter hinauf – bis zur Million. Bei jeder Auflösung wird das
Albumcover eingeblendet.

- **Backend:** Python + FastAPI (Antwortprüfung passiert serverseitig)
- **Frontend:** React + TypeScript + Vite
- **Sounds:** komplett über die Web Audio API synthetisiert – keine Audiodateien
- **Albumcover:** generierte SVGs, ausschließlich in `backend/static/covers/`

## Features

| Feature | Beschreibung |
|---|---|
| 15 Stufen | Von 50 € bis 1.000.000 €, Schwierigkeit steigt kontinuierlich |
| Sicherheitsstufen | Bei 500 € (Stufe 5) und 16.000 € (Stufe 10) |
| 45 Fragen | 3 pro Stufe, pro Runde zufällig gezogen und gemischt |
| 3 Joker | Fifty-Fifty, Publikumsjoker, Skip |
| Aussteigen | Gewinn jederzeit ab Stufe 2 sichern |
| Cover-Reveal | Albumcover, Track, Album, Jahr und ein Fun-Fact nach jeder Antwort |
| Funky Sounds | Arpeggio bei richtig, Bass-Wobble + Scratch bei falsch, Fanfare bei der Million |
| Reload-fest | Laufende Session wird über `localStorage` wiederhergestellt |

Schwierigkeitskurve: Stufe 1–5 Chart-Hits (Sido, Capital Bra, Haftbefehl),
6–10 Album-Deep-Cuts (Kool Savas, Trettmann, Torch), 11–15 Underground und
Old School (Advanced Chemistry, Fischmob, Fresh Familee 1991).

## Setup

Voraussetzungen: Python ≥ 3.11, Node ≥ 18.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python tools/gen_covers.py      # erzeugt die Albumcover
uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

Der Vite-Dev-Server proxied `/api` und `/covers` auf Port 8000.

### Produktion

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app
```

Liegt `frontend/dist/`, liefert FastAPI das Frontend unter `/` gleich mit aus –
ein einziger Prozess auf Port 8000.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -q
```

Abgedeckt: Datenqualität des Katalogs, Existenz aller Cover, kompletter
Durchlauf bis zur Million, Sicherheitsstufen-Logik, Cash-out, alle drei Joker
und die Zusicherung, dass die Lösung nie an den Client geht, bevor geantwortet
wurde.

### Visueller Test

Klickt das Quiz mit Playwright wie ein echter User durch, prüft dabei, ob die
Albumcover tatsächlich laden, und legt Screenshots in `/tmp/shots` ab:

```bash
cd backend && uvicorn app.main:app --port 8014 &   # Frontend vorher bauen
cd frontend && npm run shots
```

Der Lauf schlägt fehl, sobald ein Cover nicht lädt oder ein Konsolen- bzw.
Netzwerkfehler auftritt.

## API

| Methode | Pfad | Zweck |
|---|---|---|
| `POST` | `/api/game` | Neue Runde starten |
| `GET` | `/api/game/{id}` | Aktuellen Spielzustand abrufen |
| `POST` | `/api/game/{id}/answer` | Antwort prüfen, Song aufdecken |
| `POST` | `/api/game/{id}/lifeline` | Joker einsetzen |
| `POST` | `/api/game/{id}/cashout` | Aussteigen |
| `GET` | `/covers/{datei}.svg` | Albumcover |
| `GET` | `/docs` | Interaktive OpenAPI-Doku |

Die richtige Antwort verlässt den Server erst mit der Antwort auf
`/answer` – Cheaten über die DevTools ist damit nicht möglich.

## Projektstruktur

```
backend/
├── app/
│   ├── main.py            FastAPI-App, CORS, Static Mounts
│   ├── models.py          Pydantic-Schemas
│   ├── game.py            Gewinnleiter, Sessions, Joker
│   ├── routes.py          API-Endpunkte
│   └── data/questions.py  Fragenkatalog
├── static/covers/         NUR Albumcover (44 SVGs)
├── tools/gen_covers.py    Cover-Generator
└── tests/test_api.py

frontend/src/
├── App.tsx                Spielzustandsmaschine
├── api.ts  types.ts       API-Client
├── audio/sfx.ts           Web-Audio-Sound-Engine
└── components/            Ladder, AnswerButton, CoverReveal, Lifelines, …
```

## Fragen ergänzen

Neuen Eintrag in `backend/app/data/questions.py` in die Liste `RAW` einfügen
(`level`, `line`, `answers`, `correct`, `artist`, `track`, `album`, `year`,
`fun_fact`), danach `python tools/gen_covers.py` ausführen – der Cover-Name wird
automatisch aus Artist und Album abgeleitet und die Grafik erzeugt. Verwaiste
Cover werden dabei entfernt, der Ordner bleibt sauber.

Echte Cover können jederzeit als `backend/static/covers/<artist>--<album>.svg`
hinterlegt werden; der Generator überschreibt sie allerdings beim nächsten Lauf.

## Rechtliches

Es werden ausschließlich kurze Zitatfragmente im Rahmen des Zitatrechts
(§ 51 UrhG) verwendet. Die Albumcover sind eigens generierte SVG-Grafiken und
keine Reproduktionen der Originalcover.
