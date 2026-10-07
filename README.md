# Wer wird Rapmillionär – Deutschrap-Quiz

Ein Quiz im Stil von „Wer wird Millionär": Eine bekannte Line aus dem deutschen
Rap wird gezeigt, drei Künstler stehen zur Auswahl. Wer richtig liegt, steigt
die Gewinnleiter hinauf – bis zur Million. Bei jeder Auflösung werden Track,
Album, Jahr, Albumcover und ein Link zum vollständigen Songtext eingeblendet.

| Bereich | Technik |
|---|---|
| Backend | Python ≥ 3.11, FastAPI, Pydantic v2 – Antwortprüfung passiert serverseitig |
| Frontend | React 18, TypeScript (strict), Vite 6 |
| Sounds | Komplett über die Web Audio API synthetisiert – keine Audiodateien |
| Albumcover | Generierte SVGs, ausschließlich in `backend/static/covers/` |
| Tests | pytest (API + Katalog), Playwright (visueller Smoke-Test) |

> Für KI-Agenten und neue Mitwirkende: Arbeitsregeln, Invarianten und Fallstricke
> stehen in [`AGENTS.md`](AGENTS.md).

## Schnellstart

Voraussetzungen: Python ≥ 3.11, Node ≥ 18.

```bash
./start.sh          # Produktion: baut das Frontend, alles auf http://127.0.0.1:8000
./start.sh --dev    # Entwicklung: Backend mit --reload (:8000) + Vite (:5173)
PORT=9000 ./start.sh
```

Das Skript legt beim ersten Lauf venv und `node_modules` selbst an und baut
das Frontend nur neu, wenn sich die Quellen geändert haben. Manuell geht es so:

```bash
# Terminal 1 – Backend (http://127.0.0.1:8000, API-Doku unter /docs)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Terminal 2 – Frontend (http://localhost:5173)
cd frontend
npm install
npm run dev
```

Der Vite-Dev-Server proxied `/api` und `/covers` auf Port 8000. Die Cover sind
eingecheckt; `python tools/gen_covers.py` ist nur nach Katalogänderungen nötig.

### Produktion

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app
```

Existiert `frontend/dist/`, liefert FastAPI das Frontend unter `/` gleich mit aus –
ein einziger Prozess auf Port 8000.

## Features

| Feature | Beschreibung |
|---|---|
| 15 Stufen | Von 50 € bis 1.000.000 €, Schwierigkeit steigt kontinuierlich |
| Sicherheitsstufen | Bei 500 € (Stufe 5) und 16.000 € (Stufe 10) |
| 135+ Fragen | mindestens 9 pro Stufe, pro Runde zufällig gezogen, Antworten gemischt |
| Belegte Zitate | Jede Zeile ist wörtlich gegen ihre Genius-Quelle verifiziert |
| 3 Joker | Fifty-Fifty, Publikumsjoker, Skip (neue Frage auf gleicher Stufe) |
| Aussteigen | Gewinn jederzeit sichern |
| Cover-Reveal | Albumcover, Track, Album, Jahr und Quellenlink nach jeder Antwort |
| Funky Sounds | Arpeggio bei richtig, Bass-Wobble + Scratch bei falsch, Fanfare bei der Million |
| Runde fortsetzen | Die Session-ID liegt in `localStorage`; eine laufende Runde wird auf dem Startbildschirm zum Fortsetzen angeboten (nicht automatisch geladen) |

Schwierigkeitskurve: Stufe 1–5 Chart-Hits (Apache 207, Haftbefehl, Bausa, Juju,
SSIO), 6–10 bekannte Punchlines und Szenegrößen (K.I.Z, Kollegah, OG Keemo,
Antilopen Gang, Haiyti), 11–15 Klassiker und Underground (Advanced Chemistry
1992, Torch, Morlockk Dilemma, Huss und Hodn, Absztrakkt, Main Concept).

## Architektur

```
Browser (React)  ──/api──▶  FastAPI (routes.py)  ──▶  game.py (Session, Joker, Leiter)
       │                                                   │
       └──/covers──▶  StaticFiles(backend/static/covers)   └──▶ data/questions.py (Katalog)
```

- **Sessions** liegen im Speicher (`SessionStore` in `game.py`, TTL 6 h). Ein
  Neustart des Backends verwirft alle laufenden Runden. Der Store ist hinter
  einem schmalen Interface gekapselt, damit später Redis/SQLite möglich ist.
- **Die Lösung verlässt den Server erst mit der Antwort auf `/answer`.** Der
  Client bekommt nur `PublicQuestion` (ohne `correct_index`) – Cheaten über die
  DevTools ist nicht möglich.
- **Typen** existieren doppelt: Pydantic in `backend/app/models.py`, TypeScript
  in `frontend/src/types.ts`. Beide müssen synchron gehalten werden.

### API

| Methode | Pfad | Zweck |
|---|---|---|
| `POST` | `/api/game` | Neue Runde starten (201) |
| `GET` | `/api/game/{id}` | Aktuellen Spielzustand abrufen |
| `POST` | `/api/game/{id}/answer` | Antwort prüfen (`{"answer_index": 0-2}`), Song aufdecken |
| `POST` | `/api/game/{id}/lifeline` | Joker einsetzen (`fifty_fifty` \| `publikum` \| `skip`) |
| `POST` | `/api/game/{id}/cashout` | Aussteigen |
| `GET` | `/api/health` | Health-Check |
| `GET` | `/covers/{datei}.svg` | Albumcover |
| `GET` | `/docs` | Interaktive OpenAPI-Doku |

Fehler: `404` für unbekannte Sessions, `409` für fachlich ungültige Aktionen
(Spiel beendet, Joker verbraucht).

### Projektstruktur

```
backend/
├── app/
│   ├── main.py            FastAPI-App, CORS, Static Mounts (Cover + optional dist/)
│   ├── models.py          Pydantic-Schemas
│   ├── game.py            Gewinnleiter, Sicherheitsstufen, Sessions, Joker
│   ├── routes.py          API-Endpunkte
│   └── data/questions.py  Fragenkatalog (Liste RAW)
├── static/covers/         NUR Albumcover (generierte SVGs, eingecheckt)
├── tools/
│   ├── gen_covers.py      Cover-Generator (deterministisch, entfernt verwaiste Cover)
│   └── verify_sources.py  Quellenprüfung der Zitate gegen Genius
└── tests/test_api.py      Katalog- und API-Tests

frontend/
├── src/
│   ├── App.tsx            Spielzustandsmaschine
│   ├── api.ts  types.ts   API-Client und Typen
│   ├── audio/sfx.ts       Web-Audio-Sound-Engine
│   └── components/        StartScreen, Ladder, AnswerButton, Lifelines, CoverReveal, GameOver
├── scripts/screenshot.mjs Playwright-Smoke-Test
└── vite.config.ts         Dev-Proxy auf :8000
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -q

cd ../frontend
npm run typecheck
```

Abgedeckt: Datenqualität des Katalogs (mindestens 9 Fragen pro Stufe, drei
eindeutige Antworten, Künstlername nicht in der Zeile, keine doppelten Zeilen
oder Songs), Quellenpflicht, Existenz aller Cover, kompletter Durchlauf bis zur
Million, Sicherheitsstufen, Cash-out, alle drei Joker und die Zusicherung, dass
die Lösung nie vor der Antwort an den Client geht.

### Quellenprüfung

Lädt die Genius-Seiten (Netzwerk nötig) und schlägt fehl, sobald eine Zeile
dort nicht wörtlich auffindbar ist:

```bash
cd backend
python tools/verify_sources.py          # alle Einträge
python tools/verify_sources.py q003     # einzelne IDs
```

Aktueller Stand: **135/135 Zeilen wörtlich belegt.**

Dieses Skript existiert aus gutem Grund: Eine frühere Fassung des Katalogs
enthielt 43 von 45 **frei erfundenen** Zeilen sowie zahlreiche falsche Alben und
Jahreszahlen. Der Katalog wurde daraufhin vollständig neu aufgebaut. `source`
ist seitdem Pflichtfeld, und `tests/test_api.py` lehnt Einträge ohne
Genius-Quelle ab.

### Visueller Test

Klickt das Quiz mit Playwright wie ein echter User durch, prüft, ob die
Albumcover tatsächlich laden, und legt Screenshots in `/tmp/shots` ab:

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --port 8014 &
cd ../frontend && npx playwright install chromium   # einmalig
npm run shots                                       # QUIZ_URL überschreibt die Ziel-URL
```

Der Lauf schlägt fehl, sobald ein Cover nicht lädt oder ein Konsolen- bzw.
Netzwerkfehler auftritt.

## Fragen ergänzen

Neuen Eintrag in `backend/app/data/questions.py` in die Liste `RAW` einfügen:

```python
{
    "level": 7,                      # 1–15
    "line": "…",                     # buchstabengetreu von der Quelle
    "answers": ["Richtig", "Falsch A", "Falsch B"],
    "correct": 0,                    # answers[correct] muss == artist sein
    "artist": "Richtig",
    "track": "…",
    "album": "…",
    "year": 2015,
    "source": G + "Artist-track-lyrics",
},
```

Danach:

```bash
python tools/gen_covers.py        # erzeugt das Cover
python tools/verify_sources.py    # belegt die Zeile gegen die Quelle
python -m pytest tests -q
```

**Regeln:**

- Die Zeile muss buchstabengetreu von der unter `source` angegebenen Seite
  stammen. Nichts aus dem Gedächtnis zitieren.
- Jede Stufe braucht mindestens 9 Fragen (Test erzwingt das); die Stufen dürfen
  unterschiedlich groß sein.
- Fragen-IDs (`q001` …) ergeben sich aus der Position in `RAW`. Einfügen in der
  Mitte verschiebt alle folgenden IDs.
- Der Cover-Dateiname wird automatisch aus Artist und Album abgeleitet
  (`<artist>--<album>.svg`), verwaiste Cover werden vom Generator entfernt.

## Herkunft der Zitate

Die Auswahl kombiniert zwei Signale:

- **Genius-Views** als Bekanntheitsmaß — steuert, auf welcher Stufe eine Zeile landet
- **Hoch geupvotete Punchline-Threads aus r/GermanRap** — Community-Relevanz

Reddit-Zitate wurden ausnahmslos gegen Genius geprüft, weil dort fast immer aus
dem Gedächtnis und damit ungenau zitiert wird (Beispiel: „Du hast mehr Väter als
griechischer Salat" heißt im Original „Du Verräter hast mehr Väter als
griechischer Salat").

**Inhaltsfilter:** Derbe, vulgäre und misogyne Zeilen sind bewusst enthalten —
sie gehören zum Genre. Ausgeschlossen sind homophobe Slurs, fremdenfeindliche
und rassistische Begriffe, NS-Vergleiche sowie „behindert"/„Spast" als
Beleidigung.

Der Filter greift nicht nur auf die zitierte Zeile, sondern auf den **gesamten
Songtext**. Gerade im Berliner Battle Rap führte das zu vielen Ausweichfällen —
bei MC Bomber, Taktloss, B-Tight, MOK, SpongeBOZZ, 4tune und Bass Sultan Hengzt
mussten die jeweils meistgesehenen Songs verworfen und ein sauberer Track
desselben Künstlers gewählt werden. Die Prüfung erfolgt bei der Aufnahme neuer
Zeilen; im Repository existiert dafür (noch) kein automatisiertes Skript.

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
