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
| 75 Fragen | 5 pro Stufe, pro Runde zufällig gezogen und gemischt |
| Belegte Zitate | Jede Zeile ist wörtlich gegen ihre Genius-Quelle verifiziert |
| 3 Joker | Fifty-Fifty, Publikumsjoker, Skip |
| Aussteigen | Gewinn jederzeit ab Stufe 2 sichern |
| Cover-Reveal | Albumcover, Track, Album, Jahr und Quellenlink nach jeder Antwort |
| Funky Sounds | Arpeggio bei richtig, Bass-Wobble + Scratch bei falsch, Fanfare bei der Million |
| Reload-fest | Laufende Session wird über `localStorage` wiederhergestellt |

Schwierigkeitskurve: Stufe 1–5 Chart-Hits (Apache 207, Haftbefehl, Bausa),
6–10 bekannte Punchlines (K.I.Z, Kollegah, SSIO), 11–15 Klassiker und
Underground (Advanced Chemistry 1992, Torch, Massive Töne, Doppelkopf).

## Herkunft der Zitate

Die Auswahl kombiniert zwei Signale:

- **Genius-Views** als Bekanntheitsmaß — steuert, auf welcher Stufe eine Zeile landet
- **Hoch geupvotete Punchline-Threads aus r/GermanRap** — Community-Relevanz

Reddit-Zitate wurden ausnahmslos gegen Genius geprüft, weil dort fast immer aus
dem Gedächtnis und damit ungenau zitiert wird (Beispiel: „Du hast mehr Väter als
griechischer Salat" heißt im Original „Du Verräter hast mehr Väter als
griechischer Salat").

**Inhaltsfilter:** Derbe, vulgäre und misogyne Zeilen sind bewusst enthalten —
sie gehören zum Genre. Ausgeschlossen wurden homophobe und fremdenfeindliche
Zeilen.

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

Abgedeckt: Datenqualität des Katalogs, Quellenpflicht, Existenz aller Cover,
kompletter Durchlauf bis zur Million, Sicherheitsstufen-Logik, Cash-out, alle
drei Joker und die Zusicherung, dass die Lösung nie an den Client geht, bevor
geantwortet wurde. Zusätzlich wird geprüft, dass keine Zeile den Künstlernamen
enthält und kein Song doppelt vorkommt.

### Quellenprüfung

Fährt alle 45 Zeilen gegen ihre Genius-Seiten und schlägt fehl, sobald eine
Zeile dort nicht wörtlich auffindbar ist:

```bash
cd backend
python tools/verify_sources.py          # alle 75 Einträge
python tools/verify_sources.py q003     # einzelne ID
```

Aktueller Stand: **75/75 Zeilen wörtlich belegt.**

Dieses Skript existiert aus gutem Grund: Eine frühere Fassung des Katalogs
enthielt 43 von 45 **frei erfundenen** Zeilen sowie zahlreiche falsche Alben und
Jahreszahlen. Der Katalog wurde daraufhin vollständig neu aufgebaut. `source_url`
ist seitdem Pflichtfeld, und `tests/test_api.py` lehnt Einträge ohne Quelle ab.

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
├── tools/
│   ├── gen_covers.py      Cover-Generator
│   └── verify_sources.py  Quellenprüfung der Zitate
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
`source`). Danach:

```bash
python tools/gen_covers.py        # erzeugt das Cover
python tools/verify_sources.py    # belegt die Zeile gegen die Quelle
python -m pytest tests -q
```

**Regel:** Die Zeile muss buchstabengetreu von der unter `source` angegebenen
Seite stammen. Nichts aus dem Gedächtnis zitieren – `verify_sources.py` fällt
sonst durch. Der Cover-Name wird automatisch aus Artist und Album abgeleitet,
verwaiste Cover werden entfernt.

Echte Cover können jederzeit als `backend/static/covers/<artist>--<album>.svg`
hinterlegt werden; der Generator überschreibt sie allerdings beim nächsten Lauf.

## Rechtliches

Es werden ausschließlich kurze Zitatfragmente im Rahmen des Zitatrechts
(§ 51 UrhG) verwendet, jeweils mit Quellenangabe und Link zum vollständigen
Songtext.

### Warum generierte Cover statt echter Albumcover?

Die Frage, ob echte Cover über Wikimedia bezogen werden können, wurde geprüft.
Das Ergebnis: **nein.**

| Quelle | Befund |
|---|---|
| Wikimedia Commons | Verbietet Cover-Scans strukturell. Erlaubt sind nur frei lizenzierte Werke; „album/CD covers" sind ausdrücklich als unzulässig gelistet. Von 12 geprüften Alben waren nur 4 vorhanden – Sonderfreigaben von Aggro Berlin und Selfmade Records. |
| Deutsche Wikipedia | Hat keine Fair-Use-Ausnahme. Nicht-freie Cover sind dort generell unzulässig. |
| Englische Wikipedia | Hostet Cover lokal unter US-Fair-Use. Diese Dateien bleiben voll geschützt, es wird **keine** Weiterlizenz erteilt – eine Nutzung in dieser App wäre rechtswidrig, zumal das deutsche UrhG kein Fair Use kennt. |

Deshalb bleibt es bei den generierten SVGs in `backend/static/covers/`.

**Legale Alternative, falls echte Bilder gewünscht sind:** Für praktisch alle
Künstler existieren auf Commons frei lizenzierte **Fotos** (CC BY-SA), z. B.
Live- und Pressebilder. Damit ließe sich das Reveal statt mit dem Cover mit
einem Künstlerporträt gestalten – Pflicht wären Urhebernennung, Lizenzangabe
und Lizenz-Link am Bild. Zu beachten wäre zusätzlich das Recht am eigenen Bild
(§ 22 KUG), sobald die App kommerziell genutzt wird.

Der andere saubere Weg wären offizielle Musik-APIs (Spotify, Apple Music,
Cover Art Archive) unter deren Nutzungsbedingungen.
