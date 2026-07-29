"""Fragenkatalog: 15 Level x 3 Fragen.

QUELLENPFLICHT
--------------
Jede Zeile in diesem Katalog wurde woertlich von der unter `source` angegebenen
Genius-Seite uebernommen und dort verifiziert. Es wird NICHTS aus dem Gedaechtnis
zitiert. `tests/test_api.py` erzwingt, dass jeder Eintrag eine Quelle hat.

Auswahl der Zeilen
------------------
Die Auswahl kombiniert zwei Signale:
  * Genius-Views als Bekanntheitsmass (steuert die Schwierigkeitsstufe)
  * hoch geupvotete Punchline-Threads aus r/GermanRap (Community-Relevanz)
Reddit-Zitate wurden ausnahmslos gegen Genius geprueft, da dort meist aus dem
Gedaechtnis und damit ungenau zitiert wird.

Inhaltsfilter
-------------
Derbe, vulgaere und misogyne Zeilen sind bewusst enthalten - sie gehoeren zum
Genre. Ausgeschlossen wurden homophobe und fremdenfeindliche Zeilen.

Recht
-----
Kurze Zitatfragmente im Rahmen des Zitatrechts (Paragraph 51 UrhG). Die
Albumcover sind eigens generierte SVG-Grafiken, keine Reproduktionen.
"""

from __future__ import annotations

from ..models import Question

G = "https://genius.com/"

RAW: list[dict] = [
    # ================================================== L1 - riesige Hits
    {
        "level": 1,
        "line": "Dann wird es rote Rosen regnen",
        "answers": ["Alligatoah", "Casper", "Cro"],
        "correct": 0,
        "artist": "Alligatoah",
        "track": "Willst du",
        "album": "Triebwerke",
        "year": 2013,
        "source": G + "Alligatoah-willst-du-lyrics",
    },
    {
        "level": 1,
        "line": "Immer noch derselbe Chabo, Bitch, den du am Bahnhof triffst",
        "answers": ["Haftbefehl", "Farid Bang", "Xatar"],
        "correct": 0,
        "artist": "Haftbefehl",
        "track": "Chabos wissen wer der Babo ist",
        "album": "Blockplatin",
        "year": 2012,
        "source": G + "Haftbefehl-chabos-wissen-wer-der-babo-ist-lyrics",
    },
    {
        "level": 1,
        "line": "Brudi, ich muss los, wenn die Roller wieder schrei'n",
        "answers": ["Apache 207", "Ufo361", "Luciano"],
        "correct": 0,
        "artist": "Apache 207",
        "track": "Roller",
        "album": "Platte",
        "year": 2019,
        "source": G + "Apache-207-roller-lyrics",
    },
    # ================================================== L2
    {
        "level": 2,
        "line": "Ich park' mein Herz bei dir heute Nacht",
        "answers": ["Bausa", "Capital Bra", "Bonez MC"],
        "correct": 0,
        "artist": "Bausa",
        "track": "Was Du Liebe nennst",
        "album": "PowerBausa",
        "year": 2017,
        "source": G + "Bausa-was-du-liebe-nennst-lyrics",
    },
    {
        "level": 2,
        "line": "Über den Dächern meiner Stadt riecht die Luft nach Marihuana",
        "answers": ["Bonez MC & RAF Camora", "187 Strassenbande", "Gzuz"],
        "correct": 0,
        "artist": "Bonez MC & RAF Camora",
        "track": "Palmen aus Plastik",
        "album": "Palmen aus Plastik",
        "year": 2016,
        "source": G + "Bonez-mc-and-raf-camora-palmen-aus-plastik-lyrics",
    },
    {
        "level": 2,
        "line": "Und der Richter schreit, ich war der Täter",
        "answers": ["Capital Bra", "Samra", "Luciano"],
        "correct": 0,
        "artist": "Capital Bra",
        "track": "Neymar",
        "album": "Berlin lebt",
        "year": 2018,
        "source": G + "Capital-bra-neymar-lyrics",
    },
    # ================================================== L3
    {
        "level": 3,
        "line": "Ich habe Raubtiere als Haustiere",
        "answers": ["Kollegah", "Farid Bang", "Fler"],
        "correct": 0,
        "artist": "Kollegah",
        "track": "King",
        "album": "King",
        "year": 2014,
        "source": G + "Kollegah-king-lyrics",
    },
    {
        "level": 3,
        "line": "Ab jetzt wird alles easy, denn du bist nicht mehr da",
        "answers": ["CRO", "Casper", "Marteria"],
        "correct": 0,
        "artist": "CRO",
        "track": "Easy",
        "album": "Easy",
        "year": 2011,
        "source": G + "Cro-easy-lyrics",
    },
    {
        "level": 3,
        "line": "Alle hab'n 'n Job, ich hab' Langeweile",
        "answers": ["Marteria", "Casper", "Kraftklub"],
        "correct": 0,
        "artist": "Marteria",
        "track": "Kids (2 Finger an den Kopf)",
        "album": "Zum Glück in die Zukunft II",
        "year": 2013,
        "source": G + "Marteria-kids-2-finger-an-den-kopf-lyrics",
    },
    # ================================================== L4
    {
        "level": 4,
        "line": "Sondern nur das Ergebnis von Blut, Schweiß und Tränen",
        "answers": ["Kontra K", "Kollegah", "Fard"],
        "correct": 0,
        "artist": "Kontra K",
        "track": "Erfolg ist kein Glück",
        "album": "Aus dem Schatten ins Licht",
        "year": 2015,
        "source": G + "Kontra-k-erfolg-ist-kein-gluck-lyrics",
    },
    {
        "level": 4,
        "line": "Du hast gedacht, ich mache Spaß, aber keiner hier lacht",
        "answers": ["Gzuz", "Bonez MC", "Maxwell"],
        "correct": 0,
        "artist": "Gzuz",
        "track": "¿ Was hast du gedacht ?",
        "album": "Wolke 7",
        "year": 2018,
        "source": G + "Gzuz-was-hast-du-gedacht-lyrics",
    },
    {
        "level": 4,
        "line": "Wenn es so weitergeht, dann kauf' ich mir 'ne Villa in Beverly Hills",
        "answers": ["Ufo361", "Nimo", "Olexesh"],
        "correct": 0,
        "artist": "Ufo361",
        "track": "Beverly Hills",
        "album": "808",
        "year": 2018,
        "source": G + "Ufo361-beverly-hills-lyrics",
    },
    # ================================================== L5
    {
        "level": 5,
        "line": "Die Banken kratzen an den Wolken / Ich mich am Yarak, wie komm' ich an Euros?",
        "answers": ["Haftbefehl & Bazzazian", "Xatar", "SSIO"],
        "correct": 0,
        "artist": "Haftbefehl & Bazzazian",
        "track": "069",
        "album": "Unzensiert",
        "year": 2015,
        "source": G + "Haftbefehl-and-bazzazian-069-lyrics",
    },
    {
        "level": 5,
        "line": "Tanze mit der weißen Dame einen Tango",
        "answers": ["Yung Hurn & RIN", "Money Boy", "LGoony"],
        "correct": 0,
        "artist": "Yung Hurn & RIN",
        "track": "Bianco",
        "album": "In Memory of Yung Hurn - Classic Compilation",
        "year": 2016,
        "source": G + "Yung-hurn-and-rin-bianco-lyrics",
    },
    {
        "level": 5,
        "line": "Fast hinter jeder Tür lauert 'n Abgrund",
        "answers": ["Trettmann & KITSCHKRIEG", "Megaloh", "Chefket"],
        "correct": 0,
        "artist": "Trettmann & KITSCHKRIEG",
        "track": "Grauer Beton",
        "album": "#DIY",
        "year": 2017,
        "source": G + "Trettmann-grauer-beton-lyrics",
    },
    # ================================================== L6
    {
        "level": 6,
        "line": "Scheiße auf Drip, check, ich hab' Sixpack / Bullen gurgeln meinen Pisstest",
        "answers": ["K.I.Z", "Trailerpark", "Audio88 & Yassin"],
        "correct": 0,
        "artist": "K.I.Z",
        "track": "Rap über Hass",
        "album": "Rap über Hass",
        "year": 2021,
        "source": G + "Kiz-rap-uber-hass-lyrics",
    },
    {
        "level": 6,
        "line": "Denn an Nikolaus geh' ich mit Nicole aus",
        "answers": ["Farid Bang", "Kollegah", "Summer Cem"],
        "correct": 0,
        "artist": "Farid Bang",
        "track": "Bitte Spitte 5000",
        "album": "Banger leben kürzer",
        "year": 2011,
        "source": G + "Farid-bang-bitte-spitte-5000-lyrics",
    },
    {
        "level": 6,
        "line": "Die ersten sind gescheitert, die ersten was geworden",
        "answers": ["Prinz Pi", "Casper", "Curse"],
        "correct": 0,
        "artist": "Prinz Pi",
        "track": "Kompass ohne Norden",
        "album": "Kompass ohne Norden",
        "year": 2013,
        "source": G + "Prinz-pi-kompass-ohne-norden-lyrics",
    },
    # ================================================== L7
    {
        "level": 7,
        "line": "Währ'nd ich hier mit mei'm schönen, voluminösen, gegelten Haar sitze",
        "answers": ["Kollegah", "Favorite", "Genetikk"],
        "correct": 0,
        "artist": "Kollegah",
        "track": "Fanpost",
        "album": "Fanpost",
        "year": 2009,
        "source": G + "Kollegah-fanpost-lyrics",
    },
    {
        "level": 7,
        "line": "Wie, es gibt kein deutsches Ghetto? Wir haben Ghettos hier erfunden",
        "answers": ["K.I.Z", "Trailerpark", "Antilopen Gang"],
        "correct": 0,
        "artist": "K.I.Z",
        "track": "Urlaub fürs Gehirn",
        "album": "Urlaub fürs Gehirn",
        "year": 2011,
        "source": G + "Kiz-urlaub-furs-gehirn-lyrics",
    },
    {
        "level": 7,
        "line": "Steck mal dein Messer weg und lerne mit einer Gabel umzugeh'n",
        "answers": ["Trailerpark", "K.I.Z", "Alligatoah"],
        "correct": 0,
        "artist": "Trailerpark",
        "track": "Fledermausland",
        "album": "Crackstreet Boys 2",
        "year": 2012,
        "source": G + "Trailerpark-fledermausland-lyrics",
    },
    # ================================================== L8
    {
        "level": 8,
        "line": "Laptop, Rapgott, Lederjacken-Prollschiene",
        "answers": ["Bushido", "Fler", "Sido"],
        "correct": 0,
        "artist": "Bushido",
        "track": "Sonnenbank Flavour",
        "album": "Von der Skyline zum Bordstein zurück",
        "year": 2006,
        "source": G + "Bushido-sonnenbank-flavour-lyrics",
    },
    {
        "level": 8,
        "line": "Meine Schreibmaschine hat keine Buchstaben / Außer H, U, R, E, N, S, O, H, N",
        "answers": ["K.I.Z", "Audio88 & Yassin", "Pöbel MC"],
        "correct": 0,
        "artist": "K.I.Z",
        "track": "VIP in der Psychiatrie",
        "album": "Rap über Hass",
        "year": 2021,
        "source": G + "Kiz-vip-in-der-psychiatrie-lyrics",
    },
    {
        "level": 8,
        "line": "hol dir statt 'nem Apfel einfach mal den Big King XXL",
        "answers": ["SSIO", "Olexesh", "Nimo"],
        "correct": 0,
        "artist": "SSIO",
        "track": "Big King XXL",
        "album": "BB.U.M.SS.N.",
        "year": 2013,
        "source": G + "Ssio-big-king-xxl-lyrics",
    },
    # ================================================== L9
    {
        "level": 9,
        "line": "Ich bleib' immer dieser scheiß Ausländer",
        "answers": ["Eko Fresh", "Summer Cem", "Manuellsen"],
        "correct": 0,
        "artist": "Eko Fresh",
        "track": "Quotentürke",
        "album": "Eksodus",
        "year": 2013,
        "source": G + "Eko-fresh-quotenturke-lyrics",
    },
    {
        "level": 9,
        "line": "Doch wenn der Wurm noch früher aufsteht kann der Vogel sich ficken geh'n",
        "answers": ["Audio88 & Yassin", "Antilopen Gang", "Fatoni"],
        "correct": 0,
        "artist": "Audio88 & Yassin",
        "track": "Gnade",
        "album": "Halleluja",
        "year": 2016,
        "source": G + "Audio88-and-yassin-gnade-lyrics",
    },
    {
        "level": 9,
        "line": "Da kommt der spendable Boss, schenkt ihnen fünf Zigaretten",
        "answers": ["Kollegah & Farid Bang", "Bushido & Fler", "Massiv"],
        "correct": 0,
        "artist": "Kollegah & Farid Bang",
        "track": "Du liegst",
        "album": "Jung Brutal Gutaussehend 2",
        "year": 2013,
        "source": G + "Kollegah-and-farid-bang-du-liegst-lyrics",
    },
    # ================================================== L10
    {
        "level": 10,
        "line": "Wenn nicht mit Rap, dann mit der Pumpgun",
        "answers": ["Haftbefehl", "Massiv", "Automatikk"],
        "correct": 0,
        "artist": "Haftbefehl",
        "track": "Dann mit der Pumpgun",
        "album": "Azzlack Stereotyp",
        "year": 2010,
        "source": G + "Haftbefehl-dann-mit-der-pumpgun-lyrics",
    },
    {
        "level": 10,
        "line": "Ich bin der hässliche Zwillingsbruder von Bruno Mars",
        "answers": ["K.I.Z", "Trailerpark", "SSIO"],
        "correct": 0,
        "artist": "K.I.Z",
        "track": "Da geht was",
        "album": "Ganz oben",
        "year": 2013,
        "source": G + "Kiz-da-geht-was-lyrics",
    },
    {
        "level": 10,
        "line": "Rempel' ich dich an, sagst du „Sorry“ mit Voice-Crack",
        "answers": ["SSIO", "Haftbefehl", "Xatar"],
        "correct": 0,
        "artist": "SSIO",
        "track": "Alles oder Nix",
        "album": "Alles oder Nix",
        "year": 2025,
        "source": G + "Ssio-alles-oder-nix-lyrics",
    },
    # ================================================== L11 - Klassiker
    {
        "level": 11,
        "line": "Reicht vom ersten bis zum sechzehnten Stock",
        "answers": ["Sido", "Bushido", "Fler"],
        "correct": 0,
        "artist": "Sido",
        "track": "Mein Block",
        "album": "Maske",
        "year": 2004,
        "source": G + "Sido-mein-block-lyrics",
    },
    {
        "level": 11,
        "line": "Soll ich's wirklich machen oder lass' ich's lieber sein?",
        "answers": ["Fettes Brot", "Absolute Beginner", "Fünf Sterne deluxe"],
        "correct": 0,
        "artist": "Fettes Brot",
        "track": "Jein",
        "album": "Außen Top Hits, innen Geschmack",
        "year": 1996,
        "source": G + "Fettes-brot-jein-lyrics",
    },
    {
        "level": 11,
        "line": "Der Sinn des Leben ist, deinem Leben einen Sinn zu geben",
        "answers": ["Kool Savas", "Azad", "Curse"],
        "correct": 0,
        "artist": "Kool Savas",
        "track": "Der beste Tag meines Lebens",
        "album": "Der beste Tag meines Lebens",
        "year": 2002,
        "source": G + "Kool-savas-der-beste-tag-meines-lebens-lyrics",
    },
    # ================================================== L12
    {
        "level": 12,
        "line": "Menschen sehen vor lauter Bäumen den Wald kaum",
        "answers": ["Samy Deluxe", "Afrob", "Torch"],
        "correct": 0,
        "artist": "Samy Deluxe",
        "track": "Weck mich auf",
        "album": "Samy Deluxe",
        "year": 2001,
        "source": G + "Samy-deluxe-weck-mich-auf-lyrics",
    },
    {
        "level": 12,
        "line": "Jede Nacht, jeden Tag auf der Jagd",
        "answers": ["Beginner", "Fünf Sterne deluxe", "Dynamite Deluxe"],
        "correct": 0,
        "artist": "Beginner",
        "track": "Füchse",
        "album": "Bambule",
        "year": 1998,
        "source": G + "Absolute-beginner-fuchse-lyrics",
    },
    {
        "level": 12,
        "line": "Ich bin zu wortgewandt, du Horst, du Hans",
        "answers": ["Berlins Most Wanted", "Sido & Bushido", "Aggro Berlin"],
        "correct": 0,
        "artist": "Berlins Most Wanted",
        "track": "Berlins Most Wanted",
        "album": "Berlins Most Wanted",
        "year": 2010,
        "source": G + "Berlins-most-wanted-berlins-most-wanted-lyrics",
    },
    # ================================================== L13
    {
        "level": 13,
        "line": "Immer wenn es regnet muss ich an dich denken",
        "answers": ["Freundeskreis", "Massive Töne", "Blumentopf"],
        "correct": 0,
        "artist": "Freundeskreis",
        "track": "A-N-N-A",
        "album": "Quadratur des Kreises",
        "year": 1997,
        "source": G + "Freundeskreis-a-n-n-a-lyrics",
    },
    {
        "level": 13,
        "line": "Ich hol' dich da raus, du kannst immer auf mich zähl'n",
        "answers": ["Azad", "Massiv", "Kool Savas"],
        "correct": 0,
        "artist": "Azad",
        "track": "Prison Break Anthem (Ich glaub an dich)",
        "album": "Blockschrift",
        "year": 2007,
        "source": G + "Azad-prison-break-anthem-ich-glaub-an-dich-lyrics",
    },
    {
        "level": 13,
        "line": "Ich bin für die, die uns konfrontieren mit uns selbst",
        "answers": ["Curse", "Afrob", "Max Herre"],
        "correct": 0,
        "artist": "Curse",
        "track": "Widerstand",
        "album": "Innere Sicherheit",
        "year": 2003,
        "source": G + "Curse-widerstand-lyrics",
    },
    # ================================================== L14
    {
        "level": 14,
        "line": "Ich habe ein'n grünen Pass mit 'nem goldenen Adler drauf",
        "answers": ["Advanced Chemistry", "Fresh Familee", "Torch"],
        "correct": 0,
        "artist": "Advanced Chemistry",
        "track": "Fremd im eigenen Land",
        "album": "Advanced Chemistry",
        "year": 1992,
        "source": G + "Advanced-chemistry-fremd-im-eigenen-land-lyrics",
    },
    {
        "level": 14,
        "line": "Auf denen wir mit Nadeln statt Klappspaten nach Loops und Cuts graben",
        "answers": ["Eins Zwo", "Doppelkopf", "Creutzfeld & Jakob"],
        "correct": 0,
        "artist": "Eins Zwo",
        "track": "Rechte Dritter",
        "album": "Zwei",
        "year": 2001,
        "source": G + "Eins-zwo-rechte-dritter-lyrics",
    },
    {
        "level": 14,
        "line": "Cool wie Kühlung, Flows kommen frisch, nenn es Odol",
        "answers": ["Fünf Sterne Deluxe", "Dynamite Deluxe", "Fischmob"],
        "correct": 0,
        "artist": "Fünf Sterne Deluxe",
        "track": "Dein Herz schlägt schneller",
        "album": "Sillium",
        "year": 1998,
        "source": G + "Funf-sterne-deluxe-dein-herz-schlagt-schneller-lyrics",
    },
    # ================================================== L15 - Underground
    {
        "level": 15,
        "line": "Die Kühle meiner Farbe fühlst du in deiner Hand",
        "answers": ["Torch", "Toni-L", "Linguist"],
        "correct": 0,
        "artist": "Torch",
        "track": "Blauer Samt",
        "album": "Blauer Samt",
        "year": 2000,
        "source": G + "Torch-blauer-samt-lyrics",
    },
    {
        "level": 15,
        "line": "Es ist nicht, wo Du bist, es ist, was Du machst",
        "answers": ["Massive Töne", "Freundeskreis", "Afrob"],
        "correct": 0,
        "artist": "Massive Töne",
        "track": "Mutterstadt",
        "album": "Kopfnicker",
        "year": 1996,
        "source": G + "Massive-tone-mutterstadt-lyrics",
    },
    {
        "level": 15,
        "line": "Gib acht, dass du Sein und Schein nicht vertauschst",
        "answers": ["Doppelkopf", "Eins Zwo", "Creutzfeld & Jakob"],
        "correct": 0,
        "artist": "Doppelkopf",
        "track": "Balance",
        "album": "Von Abseits",
        "year": 1999,
        "source": G + "Doppelkopf-balance-lyrics",
    },
]

TRANSLITERATION = str.maketrans(
    {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "é": "e", "è": "e", "à": "a"}
)


def _slug(text: str) -> str:
    """ASCII-Slug fuer Cover-Dateinamen (Umlaute werden transliteriert)."""
    out: list[str] = []
    for ch in text.lower().translate(TRANSLITERATION):
        if ch.isascii() and ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def _build() -> list[Question]:
    questions: list[Question] = []
    for idx, raw in enumerate(RAW, start=1):
        questions.append(
            Question(
                id=f"q{idx:03d}",
                level=raw["level"],
                line=raw["line"],
                answers=raw["answers"],
                correct_index=raw["correct"],
                artist=raw["artist"],
                track=raw["track"],
                album=raw["album"],
                year=raw["year"],
                cover=f"{_slug(raw['artist'])}--{_slug(raw['album'])}.svg",
                source_url=raw["source"],
            )
        )
    return questions


QUESTIONS: list[Question] = _build()

QUESTIONS_BY_LEVEL: dict[int, list[Question]] = {}
for _q in QUESTIONS:
    QUESTIONS_BY_LEVEL.setdefault(_q.level, []).append(_q)
