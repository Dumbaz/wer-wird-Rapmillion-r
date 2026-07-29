export type GameStatus = "running" | "lost" | "won" | "cashed_out";
export type Lifeline = "fifty_fifty" | "publikum" | "skip";

export interface PublicQuestion {
  id: string;
  level: number;
  line: string;
  answers: string[];
  prize: number;
  safe_haven: boolean;
}

export interface LadderStep {
  level: number;
  prize: number;
  safe_haven: boolean;
}

export interface SongReveal {
  artist: string;
  track: string;
  album: string;
  year: number;
  cover_url: string;
  fun_fact: string;
}

export interface LifelineState {
  fifty_fifty: boolean;
  publikum: boolean;
  skip: boolean;
}

export interface GameState {
  session_id: string;
  status: GameStatus;
  level: number;
  banked: number;
  guaranteed: number;
  lifelines: LifelineState;
  ladder: LadderStep[];
  question: PublicQuestion | null;
}

export interface AnswerResult {
  correct: boolean;
  correct_index: number;
  reveal: SongReveal;
  prize_won: number;
  state: GameState;
}

export interface LifelineResult {
  lifeline: Lifeline;
  removed_indexes: number[];
  audience_votes: number[];
  state: GameState;
}
