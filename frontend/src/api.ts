import { Game, GameError, type Question, type Session } from "./game";
import type { AnswerResult, GameState, Lifeline, LifelineResult } from "./types";

/**
 * Lokale "API": Die Spiellogik läuft komplett im Browser (siehe game.ts), der
 * Katalog kommt aus questions.json. Die Signaturen entsprechen der früheren
 * HTTP-API, damit die Oberfläche unverändert bleibt.
 */

const BASE_URL = import.meta.env.BASE_URL;
const COVER_BASE = `${BASE_URL}covers`;
const STORE_KEY = "wwr-session";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let questionsPromise: Promise<Question[]> | null = null;

function loadQuestions(): Promise<Question[]> {
  questionsPromise ??= fetch(`${BASE_URL}questions.json`)
    .then((res) => {
      if (!res.ok) throw new Error(String(res.status));
      return res.json() as Promise<Question[]>;
    })
    .catch(() => {
      questionsPromise = null;
      throw new ApiError("Fragenkatalog konnte nicht geladen werden.", 0);
    });
  return questionsPromise;
}

let current: Game | null = null;

function persist(game: Game): void {
  if (game.session.status === "running") {
    localStorage.setItem(STORE_KEY, JSON.stringify(game.session));
  } else {
    localStorage.removeItem(STORE_KEY);
  }
}

async function gameFor(sessionId: string): Promise<Game> {
  if (current && current.session.id === sessionId) return current;
  const raw = localStorage.getItem(STORE_KEY);
  if (raw) {
    try {
      const session = JSON.parse(raw) as Session;
      if (session.id === sessionId) {
        current = new Game(await loadQuestions(), session);
        return current;
      }
    } catch (err) {
      if (err instanceof ApiError) throw err;
      /* defekter Spielstand: unten als nicht gefunden behandeln */
    }
  }
  throw new ApiError("Session nicht gefunden", 404);
}

async function run<T>(sessionId: string, action: (game: Game) => T): Promise<T> {
  const game = await gameFor(sessionId);
  try {
    const result = action(game);
    persist(game);
    return result;
  } catch (err) {
    if (err instanceof GameError) throw new ApiError(err.message, err.status);
    throw err;
  }
}

export const api = {
  startGame: async (): Promise<GameState> => {
    const questions = await loadQuestions();
    try {
      current = Game.create(questions);
    } catch (err) {
      if (err instanceof GameError) throw new ApiError(err.message, err.status);
      throw err;
    }
    persist(current);
    return current.state();
  },

  getGame: (sessionId: string): Promise<GameState> => run(sessionId, (g) => g.state()),

  answer: (sessionId: string, answerIndex: number): Promise<AnswerResult> =>
    run(sessionId, (g) => g.answer(answerIndex, COVER_BASE)),

  lifeline: (sessionId: string, lifeline: Lifeline): Promise<LifelineResult> =>
    run(sessionId, (g) => g.useLifeline(lifeline)),

  cashOut: (sessionId: string): Promise<GameState> => run(sessionId, (g) => g.cashOut()),
};

export const formatEuro = (amount: number) =>
  new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(amount);
