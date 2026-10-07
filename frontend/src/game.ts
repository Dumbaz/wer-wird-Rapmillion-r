/**
 * Spiellogik des Quiz, 1:1-Portierung von backend/app/game.py.
 *
 * Reine Funktionen ohne Netzwerk: Der Katalog und der Zufall werden
 * hineingereicht, damit die Logik testbar ist. Der Spielstand (`Session`) ist
 * JSON-serialisierbar und wird in localStorage gehalten.
 */

import type {
  AnswerResult,
  GameState,
  LadderStep,
  Lifeline,
  LifelineResult,
  LifelineState,
  PublicQuestion,
  SongReveal,
} from "./types";

export const MAX_LEVEL = 15;

export const PRIZES: Record<number, number> = {
  1: 50,
  2: 100,
  3: 200,
  4: 300,
  5: 500,
  6: 1_000,
  7: 2_000,
  8: 4_000,
  9: 8_000,
  10: 16_000,
  11: 32_000,
  12: 64_000,
  13: 125_000,
  14: 500_000,
  15: 1_000_000,
};

export const SAFE_HAVENS: ReadonlySet<number> = new Set([5, 10, 15]);

export const LADDER: LadderStep[] = Array.from({ length: MAX_LEVEL }, (_, i) => ({
  level: i + 1,
  prize: PRIZES[i + 1],
  safe_haven: SAFE_HAVENS.has(i + 1),
}));

/** Frage aus questions.json (enthält die Lösung). */
export interface Question {
  id: string;
  level: number;
  line: string;
  answers: string[];
  correct_index: number;
  artist: string;
  track: string;
  album: string;
  year: number;
  cover: string;
  source_url: string;
}

export class GameError extends Error {
  constructor(
    message: string,
    readonly status = 409,
  ) {
    super(message);
    this.name = "GameError";
  }
}

/** Zufallsquelle: liefert Werte in [0, 1). Austauschbar für Tests. */
export type Rng = () => number;

export interface Session {
  id: string;
  level: number;
  status: GameState["status"];
  banked: number;
  lifelines: LifelineState;
  /** Gezogene Frage-ID pro Level. */
  questionByLevel: Record<number, string>;
  /** Pro Level: Antwortreihenfolge als Liste von Original-Indizes. */
  shuffleByLevel: Record<number, number[]>;
  usedQuestionIds: string[];
}

export function guaranteedPrize(clearedLevel: number): number {
  let best = 0;
  for (const lvl of [...SAFE_HAVENS].sort((a, b) => a - b)) {
    if (lvl <= clearedLevel) best = PRIZES[lvl];
  }
  return best;
}

function randomId(rng: Rng): string {
  let out = "";
  for (let i = 0; i < 32; i++) out += Math.floor(rng() * 16).toString(16);
  return out;
}

function shuffled<T>(items: T[], rng: Rng): T[] {
  const a = [...items];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export class Game {
  private byId: Map<string, Question>;
  private byLevel: Map<number, Question[]>;

  constructor(
    readonly questions: Question[],
    readonly session: Session,
    private rng: Rng = Math.random,
  ) {
    this.byId = new Map(questions.map((q) => [q.id, q]));
    this.byLevel = new Map();
    for (const q of questions) {
      const list = this.byLevel.get(q.level) ?? [];
      list.push(q);
      this.byLevel.set(q.level, list);
    }
  }

  /** Startet eine neue Runde. */
  static create(questions: Question[], rng: Rng = Math.random): Game {
    const session: Session = {
      id: randomId(rng),
      level: 1,
      status: "running",
      banked: 0,
      lifelines: { fifty_fifty: true, publikum: true, skip: true },
      questionByLevel: {},
      shuffleByLevel: {},
      usedQuestionIds: [],
    };
    const game = new Game(questions, session, rng);
    game.currentQuestion();
    return game;
  }

  // -------------------------------------------------------------- Fragen
  private currentQuestion(): Question | null {
    const s = this.session;
    if (s.status !== "running" || s.level > MAX_LEVEL) return null;
    if (!(s.level in s.questionByLevel)) this.draw(s.level);
    return this.byId.get(s.questionByLevel[s.level]) ?? null;
  }

  private draw(level: number): void {
    const s = this.session;
    const all = this.byLevel.get(level) ?? [];
    let pool = all.filter((q) => !s.usedQuestionIds.includes(q.id));
    if (pool.length === 0) pool = all;
    if (pool.length === 0) throw new GameError(`Keine Fragen für Level ${level} hinterlegt`, 500);
    const question = pool[Math.floor(this.rng() * pool.length)];
    s.usedQuestionIds.push(question.id);
    s.questionByLevel[level] = question.id;
    s.shuffleByLevel[level] = shuffled(
      question.answers.map((_, i) => i),
      this.rng,
    );
  }

  private displayAnswers(level: number): string[] {
    const q = this.byId.get(this.session.questionByLevel[level])!;
    return this.session.shuffleByLevel[level].map((i) => q.answers[i]);
  }

  private displayCorrectIndex(level: number): number {
    const q = this.byId.get(this.session.questionByLevel[level])!;
    return this.session.shuffleByLevel[level].indexOf(q.correct_index);
  }

  // ---------------------------------------------------------------- View
  private publicQuestion(): PublicQuestion | null {
    const q = this.currentQuestion();
    if (!q) return null;
    return {
      id: q.id,
      level: q.level,
      line: q.line,
      answers: this.displayAnswers(q.level),
      prize: PRIZES[q.level],
      safe_haven: SAFE_HAVENS.has(q.level),
    };
  }

  state(): GameState {
    const s = this.session;
    return {
      session_id: s.id,
      status: s.status,
      level: Math.min(s.level, MAX_LEVEL),
      banked: s.banked,
      guaranteed: guaranteedPrize(s.level - 1),
      lifelines: { ...s.lifelines },
      ladder: LADDER,
      question: this.publicQuestion(),
    };
  }

  // ------------------------------------------------------------- Aktionen
  answer(index: number, coverBase: string): AnswerResult {
    const s = this.session;
    if (s.status !== "running") throw new GameError("Das Spiel ist bereits beendet");
    const q = this.currentQuestion();
    if (!q) throw new GameError("Keine aktive Frage");

    const correctIndex = this.displayCorrectIndex(s.level);
    const correct = index === correctIndex;

    const reveal: SongReveal = {
      artist: q.artist,
      track: q.track,
      album: q.album,
      year: q.year,
      cover_url: `${coverBase}/${q.cover}`,
      source_url: q.source_url,
    };

    let prizeWon: number;
    if (correct) {
      prizeWon = PRIZES[s.level];
      if (s.level === MAX_LEVEL) {
        s.status = "won";
        s.banked = PRIZES[MAX_LEVEL];
      } else {
        s.banked = prizeWon;
        s.level += 1;
      }
    } else {
      prizeWon = guaranteedPrize(s.level - 1);
      s.status = "lost";
      s.banked = prizeWon;
    }

    return {
      correct,
      correct_index: correctIndex,
      reveal,
      prize_won: prizeWon,
      state: this.state(),
    };
  }

  useLifeline(lifeline: Lifeline): LifelineResult {
    const s = this.session;
    if (s.status !== "running") throw new GameError("Das Spiel ist bereits beendet");
    if (!(lifeline in s.lifelines)) throw new GameError(`Unbekannter Joker: ${lifeline}`);
    if (!s.lifelines[lifeline]) throw new GameError(`Joker '${lifeline}' wurde bereits verbraucht`);
    if (!this.currentQuestion()) throw new GameError("Keine aktive Frage");

    const correct = this.displayCorrectIndex(s.level);
    const wrong = [0, 1, 2].filter((i) => i !== correct);
    let removed: number[] = [];
    let votes: number[] = [];

    if (lifeline === "fifty_fifty") {
      removed = [wrong[Math.floor(this.rng() * wrong.length)]];
    } else if (lifeline === "publikum") {
      votes = audienceVotes(correct, s.level, this.rng);
    } else {
      // Frage überspringen: neue Frage auf gleichem Level ziehen
      delete s.questionByLevel[s.level];
      delete s.shuffleByLevel[s.level];
      this.draw(s.level);
    }

    s.lifelines[lifeline] = false;
    return { lifeline, removed_indexes: removed, audience_votes: votes, state: this.state() };
  }

  cashOut(): GameState {
    const s = this.session;
    if (s.status !== "running") throw new GameError("Das Spiel ist bereits beendet");
    s.status = "cashed_out";
    s.banked = s.level > 1 ? PRIZES[s.level - 1] : 0;
    return this.state();
  }
}

/** Plausible Publikumsverteilung – je höher das Level, desto unsicherer. */
export function audienceVotes(correctIndex: number, level: number, rng: Rng): number[] {
  const confidence = Math.max(0.34, 0.92 - (level - 1) * 0.045);
  const uniform = (lo: number, hi: number) => lo + rng() * (hi - lo);
  let correctShare = uniform(confidence - 0.08, confidence + 0.05);
  correctShare = Math.min(0.95, Math.max(0.3, correctShare));

  const rest = 1 - correctShare;
  const split = uniform(0.3, 0.7);
  const shares = [0, 0, 0];
  const others = [0, 1, 2].filter((i) => i !== correctIndex);
  shares[correctIndex] = correctShare;
  shares[others[0]] = rest * split;
  shares[others[1]] = rest * (1 - split);

  const votes = shares.map((x) => Math.round(x * 100));
  votes[correctIndex] += 100 - votes.reduce((a, b) => a + b, 0);
  return votes;
}
