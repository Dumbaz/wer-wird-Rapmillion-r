# Wer wird Rapmillionär – Deutschrap-Quiz

Ein Quiz im Stil von „Wer wird Millionär": Eine bekannte Line aus dem deutschen
Rap wird gezeigt, drei Künstler stehen zur Auswahl. Wer richtig liegt, steigt
die Gewinnleiter hinauf – bis zur Million. Bei jeder Auflösung werden Track,
Album, Jahr, Albumcover und ein Link zum vollständigen Songtext eingeblendet.

| Bereich | Technik |
|---|---|
| Spiellogik | TypeScript im Browser (`frontend/src/game.ts`) – rein statische Seite, kein Server |
| Katalog | Python ≥ 3.11 + Pydantic v2 (`backend/`), wird zu `questions.json` exportiert |
| Frontend | React 18, TypeScript (strict), Vite 6 |
| Sounds | Komplett über die Web Audio API synthetisiert – keine Audiodateien |
| Albumcover | Generierte SVGs, ausschließlich in `backend/static/covers/` |
| Tests | Vitest (Spiellogik), pytest (Katalog), Playwright (visueller Smoke-Test) |

**Live:** https://dumbaz.github.io/wer-wird-Rapmillion-r/ (GitHub Pages, wird bei jedem Push auf `main` neu gebaut)

> Für KI-Agenten und neue Mitwirkende: Arbeitsregeln, Invarianten und Fallstricke
> stehen in [`AGENTS.md`](AGENTS.md).

## Schnellstart

Voraussetzungen: Python ≥ 3.11, Node ≥ 18.

```bash
./start.sh          # baut die Seite und zeigt sie auf http://127.0.0.1:4173
./start.sh --dev    # Entwicklung: Vite mit Hot Reload auf http://localhost:5173
PORT=9000 ./start.sh
```

Das Skript legt beim ersten Lauf venv und `node_modules` selbst an, exportiert
den Katalog und baut das Frontend. Manuell geht es so:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python tools/export_catalog.py     # schreibt frontend/public/questions.json + covers/

cd ../frontend
npm install
npm run dev                        # oder: npm run build && npx vite preview
```

`frontend/public/questions.json` und `frontend/public/covers/` sind Build-
Artefakte (gitignored) und werden von `export_catalog.py` erzeugt. Die Quelle
der Cover bleibt `backend/static/covers/` (eingecheckt); `python
tools/gen_covers.py` ist nur nach Katalogänderungen nötig.

### Veröffentlichung (GitHub Pages)

`.github/workflows/pages.yml` läuft bei jedem Push auf `main`: pytest,
Katalog-Export, Typecheck, Vitest, Build, Deploy. Der Build nutzt den relativen
Basispfad `./` und funktioniert damit unter jeder URL. Einmalig nötig:
Repository → *Settings → Pages → Source: GitHub Actions*.

## Features

| Feature | Beschreibung |
|---|---|
| 15 Stufen | Von 50 € bis 1.000.000 €, Schwierigkeit steigt kontinuierlich |
| Sicherheitsstufen | Bei 500 € (Stufe 5) und 16.000 € (Stufe 10) |
| 170+ Fragen | mindestens 9 pro Stufe, pro Runde zufällig gezogen, Antworten gemischt |
| Belegte Zitate | Jede Zeile ist wörtlich gegen ihre Genius-Quelle verifiziert |
| 3 Joker | Fifty-Fifty, Publikumsjoker, Skip (neue Frage auf gleicher Stufe) |
| Aussteigen | Gewinn jederzeit sichern |
| Cover-Reveal | Albumcover, Track, Album, Jahr und Quellenlink nach jeder Antwort |
| Funky Sounds | Arpeggio bei richtig, Bass-Wobble + Scratch bei falsch, Fanfare bei der Million |
| Runde fortsetzen | Der Spielstand liegt in `localStorage`; eine laufende Runde wird auf dem Startbildschirm zum Fortsetzen angeboten (nicht automatisch geladen) |

Schwierigkeitskurve: Stufe 1–5 Chart-Hits (Apache 207, Haftbefehl, Bausa, Juju,
SSIO), 6–10 bekannte Punchlines und Szenegrößen (K.I.Z, Kollegah, OG Keemo,
Antilopen Gang, Haiyti), 11–15 Klassiker und Underground (Advanced Chemistry
1992, Torch, Morlockk Dilemma, Huss und Hodn, Absztrakkt, Main Concept).

## Architektur

```
Browser (React) ──▶ api.ts ──▶ game.ts (Runde, Joker, Leiter)
       │                  └──▶ questions.json  (Export aus backend/app/data/questions.py)
       └──▶ covers/*.svg
```

- **Alles läuft im Browser.** `game.ts` ist eine reine Spiellogik ohne
  Netzwerk (Katalog und Zufall werden hineingereicht, daher gut testbar);
  `api.ts` hält die laufende Runde und speichert sie in `localStorage`.
- **Die Antworten stehen im ausgelieferten `questions.json`.** Wer die DevTools
  öffnet, kann die Lösung nachlesen. Das ist bewusst akzeptiert (Spaßquiz ohne
  Preis) und wird nicht verschleiert.
- **Der Katalog bleibt in Python** (`backend/app/data/questions.py`, Pydantic-
  Modell `Question`) und ist die einzige Quelle der Wahrheit; die Tests und die
  Quellenprüfung hängen daran. `export_catalog.py` macht daraus das JSON.
- **Typen:** `Question` (Pydantic) und `Question` in `frontend/src/game.ts`
  beschreiben dasselbe JSON und müssen synchron bleiben.

### Projektstruktur

```
backend/
├── app/
│   ├── models.py          Pydantic-Modell Question
│   └── data/questions.py  Fragenkatalog (Liste RAW)
├── static/covers/         NUR Albumcover (generierte SVGs, eingecheckt)
├── tools/
│   ├── export_catalog.py  Katalog + Cover -> frontend/public/
│   ├── gen_covers.py      Cover-Generator (deterministisch, entfernt verwaiste Cover)
│   └── verify_sources.py  Quellenprüfung der Zitate gegen Genius
└── tests/test_catalog.py  Katalog-Tests

frontend/
├── src/
│   ├── App.tsx            Spielzustandsmaschine
│   ├── game.ts            Spiellogik (Leiter, Sicherheitsstufen, Joker)
│   ├── game.test.ts       Vitest-Tests der Spiellogik
│   ├── api.ts  types.ts   lokale "API" über game.ts, Typen
│   ├── audio/sfx.ts       Web-Audio-Sound-Engine
│   └── components/        StartScreen, Ladder, AnswerButton, Lifelines, CoverReveal, GameOver
├── scripts/screenshot.mjs Playwright-Smoke-Test
└── vite.config.ts         base "./"
.github/workflows/pages.yml  Test, Build und Deploy auf GitHub Pages
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -q          # Katalogqualität

cd ../frontend
npm run typecheck
npm test                           # Vitest: Spiellogik
```

Abgedeckt: Datenqualität des Katalogs (mindestens 9 Fragen pro Stufe, drei
eindeutige Antworten, Künstlername nicht in der Zeile, keine doppelten Zeilen
oder Songs, keine personellen Überschneidungen der Optionen), Quellenpflicht,
Existenz aller Cover sowie in Vitest Gewinnleiter, Sicherheitsstufen,
Cash-out, alle drei Joker, keine Wiederholung innerhalb einer Runde, Mischung
der Antworten und Fortsetzen aus dem gespeicherten Spielstand.

### Quellenprüfung

Lädt die Genius-Seiten (Netzwerk nötig) und schlägt fehl, sobald eine Zeile
dort nicht wörtlich auffindbar ist:

```bash
cd backend
python tools/verify_sources.py          # alle Einträge
python tools/verify_sources.py q003     # einzelne IDs
```

Neue Einträge werden bei der Aufnahme mit diesem Skript geprüft.

Dieses Skript existiert aus gutem Grund: Eine frühere Fassung des Katalogs
enthielt 43 von 45 **frei erfundenen** Zeilen sowie zahlreiche falsche Alben und
Jahreszahlen. Der Katalog wurde daraufhin vollständig neu aufgebaut. `source`
ist seitdem Pflichtfeld, und `tests/test_catalog.py` lehnt Einträge ohne
Genius-Quelle ab.

### Visueller Test

Klickt das Quiz mit Playwright wie ein echter User durch, prüft, ob die
Albumcover tatsächlich laden, und legt Screenshots in `/tmp/shots` ab:

```bash
./start.sh &                                        # Seite auf :4173
cd frontend && npx playwright install chromium      # einmalig
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
python tools/gen_covers.py        # erzeugt das Cover (danach export_catalog.py)
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
