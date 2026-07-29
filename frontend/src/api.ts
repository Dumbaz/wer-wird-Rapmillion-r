import type { AnswerResult, GameState, Lifeline, LifelineResult } from "./types";

const BASE = "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError("Backend nicht erreichbar. Läuft uvicorn auf Port 8000?", 0);
  }

  if (!response.ok) {
    let detail = `Fehler ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* Antwort war kein JSON */
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export const api = {
  startGame: () => request<GameState>("/game", { method: "POST" }),

  getGame: (sessionId: string) => request<GameState>(`/game/${sessionId}`),

  answer: (sessionId: string, answerIndex: number) =>
    request<AnswerResult>(`/game/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ answer_index: answerIndex }),
    }),

  lifeline: (sessionId: string, lifeline: Lifeline) =>
    request<LifelineResult>(`/game/${sessionId}/lifeline`, {
      method: "POST",
      body: JSON.stringify({ lifeline }),
    }),

  cashOut: (sessionId: string) =>
    request<GameState>(`/game/${sessionId}/cashout`, { method: "POST" }),
};

export const formatEuro = (amount: number) =>
  new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(amount);
