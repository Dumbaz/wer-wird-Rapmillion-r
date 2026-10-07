import { beforeEach, describe, expect, it } from "vitest";
import {
  Game,
  GameError,
  LADDER,
  MAX_LEVEL,
  PRIZES,
  audienceVotes,
  guaranteedPrize,
  type Question,
  type Rng,
} from "./game";

/** Deterministischer Zufall (mulberry32). */
function seeded(seed: number): Rng {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Kleiner Testkatalog: 3 Fragen je Level, Lösung immer Original-Index 0. */
function catalog(perLevel = 3): Question[] {
  const out: Question[] = [];
  for (let level = 1; level <= MAX_LEVEL; level++) {
    for (let n = 0; n < perLevel; n++) {
      out.push({
        id: `q${level}-${n}`,
        level,
        line: `Zeile ${level}-${n}`,
        answers: [`Richtig ${level}-${n}`, `Falsch A ${level}-${n}`, `Falsch B ${level}-${n}`],
        correct_index: 0,
        artist: `Richtig ${level}-${n}`,
        track: "Track",
        album: "Album",
        year: 2000,
        cover: "x.svg",
        source_url: "https://genius.com/x-lyrics",
      });
    }
  }
  return out;
}

const correctIndex = (g: Game) =>
  g.state().question!.answers.findIndex((a) => a.startsWith("Richtig"));
const wrongIndex = (g: Game) => (correctIndex(g) + 1) % 3;

let game: Game;
beforeEach(() => {
  game = Game.create(catalog(), seeded(42));
});

describe("Gewinnleiter", () => {
  it("steigt monoton bis zur Million", () => {
    const prizes = LADDER.map((s) => s.prize);
    expect(prizes).toEqual([...prizes].sort((a, b) => a - b));
    expect(prizes.at(-1)).toBe(1_000_000);
    expect(LADDER.filter((s) => s.safe_haven).map((s) => s.level)).toEqual([5, 10, 15]);
  });

  it("garantierter Betrag folgt den Sicherheitsstufen", () => {
    expect(guaranteedPrize(0)).toBe(0);
    expect(guaranteedPrize(4)).toBe(0);
    expect(guaranteedPrize(5)).toBe(PRIZES[5]);
    expect(guaranteedPrize(9)).toBe(PRIZES[5]);
    expect(guaranteedPrize(10)).toBe(PRIZES[10]);
  });
});

describe("Spielstart", () => {
  it("liefert eine Frage ohne Lösung auf Level 1", () => {
    const state = game.state();
    expect(state.status).toBe("running");
    expect(state.level).toBe(1);
    expect(state.question!.answers).toHaveLength(3);
    expect(state.question).not.toHaveProperty("correct_index");
    expect(state.lifelines).toEqual({ fifty_fifty: true, publikum: true, skip: true });
  });

  it("mischt die Antworten (Lösung nicht immer an derselben Position)", () => {
    const positions = new Set<number>();
    for (let i = 0; i < 30; i++) positions.add(correctIndex(Game.create(catalog(), seeded(i))));
    expect(positions.size).toBeGreaterThan(1);
  });
});

describe("Antworten", () => {
  it("kompletter Durchlauf bis zur Million", () => {
    for (let level = 1; level <= MAX_LEVEL; level++) {
      const res = game.answer(correctIndex(game), "/covers");
      expect(res.correct).toBe(true);
      expect(res.prize_won).toBe(PRIZES[level]);
      expect(res.reveal.cover_url).toBe("/covers/x.svg");
    }
    expect(game.state().status).toBe("won");
    expect(game.state().banked).toBe(1_000_000);
  });

  it("falsche Antwort beendet das Spiel und deckt die Lösung auf", () => {
    const wrong = wrongIndex(game);
    const res = game.answer(wrong, "/covers");
    expect(res.correct).toBe(false);
    expect(res.correct_index).not.toBe(wrong);
    expect(game.state().status).toBe("lost");
    expect(() => game.answer(0, "/covers")).toThrow(GameError);
  });

  it("Sicherheitsstufe sichert den Gewinn", () => {
    for (let i = 0; i < 5; i++) game.answer(correctIndex(game), "/covers");
    const res = game.answer(wrongIndex(game), "/covers");
    expect(res.prize_won).toBe(PRIZES[5]);
    expect(game.state().banked).toBe(PRIZES[5]);
  });

  it("zieht pro Runde keine Frage doppelt, solange Auswahl da ist", () => {
    const ids = new Set<string>();
    for (let level = 1; level <= MAX_LEVEL; level++) {
      ids.add(game.state().question!.id);
      if (level < MAX_LEVEL) game.answer(correctIndex(game), "/covers");
    }
    expect(ids.size).toBe(MAX_LEVEL);
  });
});

describe("Aussteigen", () => {
  it("sichert den bisher erspielten Betrag", () => {
    for (let i = 0; i < 3; i++) game.answer(correctIndex(game), "/covers");
    const final = game.cashOut();
    expect(final.status).toBe("cashed_out");
    expect(final.banked).toBe(PRIZES[3]);
    expect(() => game.cashOut()).toThrow(GameError);
  });

  it("auf Level 1 gibt es nichts zu sichern", () => {
    expect(game.cashOut().banked).toBe(0);
  });
});

describe("Joker", () => {
  it("50:50 entfernt genau eine falsche Antwort", () => {
    const res = game.useLifeline("fifty_fifty");
    expect(res.removed_indexes).toHaveLength(1);
    expect(res.removed_indexes[0]).not.toBe(correctIndex(game));
    expect(res.state.lifelines.fifty_fifty).toBe(false);
    expect(() => game.useLifeline("fifty_fifty")).toThrow(GameError);
  });

  it("Publikum ergibt 100 Prozent und favorisiert meist die Lösung", () => {
    const votes = game.useLifeline("publikum").audience_votes;
    expect(votes.reduce((a, b) => a + b, 0)).toBe(100);
    expect(votes[correctIndex(game)]).toBe(Math.max(...votes));
  });

  it("Publikumsverteilung ist für jedes Level und jeden Seed gültig", () => {
    for (let level = 1; level <= MAX_LEVEL; level++) {
      for (let seed = 0; seed < 50; seed++) {
        const v = audienceVotes(seed % 3, level, seeded(seed));
        expect(v.reduce((a, b) => a + b, 0)).toBe(100);
        expect(Math.min(...v)).toBeGreaterThanOrEqual(0);
      }
    }
  });

  it("Skip zieht eine neue Frage auf demselben Level", () => {
    const before = game.state().question!;
    const res = game.useLifeline("skip");
    const after = res.state.question!;
    expect(after.level).toBe(before.level);
    expect(after.id).not.toBe(before.id);
    expect(res.state.lifelines.skip).toBe(false);
  });

  it.each(["fifty_fifty", "publikum", "skip"] as const)(
    "%s ist nach Spielende nicht mehr nutzbar",
    (lifeline) => {
      game.answer(wrongIndex(game), "/covers");
      expect(() => game.useLifeline(lifeline)).toThrow(GameError);
    },
  );
});

describe("Spielstand", () => {
  it("ist JSON-serialisierbar und setzt dieselbe Frage fort", () => {
    game.answer(correctIndex(game), "/covers");
    const saved = JSON.parse(JSON.stringify(game.session));
    const restored = new Game(catalog(), saved, seeded(1));
    expect(restored.state()).toEqual(game.state());
  });
});
