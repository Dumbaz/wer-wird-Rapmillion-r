import { formatEuro } from "../api";
import type { GameStatus } from "../types";

interface Props {
  status: GameStatus;
  banked: number;
  reachedLevel: number;
  onRestart: () => void;
}

const HEADLINES: Record<Exclude<GameStatus, "running">, string> = {
  won: "Rapmillionär!",
  lost: "Game Over",
  cashed_out: "Ausgestiegen",
};

const SUBLINES: Record<Exclude<GameStatus, "running">, string> = {
  won: "Alle 15 Stufen geknackt. Du kennst jede Line von Fresh Familee bis Capital Bra.",
  lost: "Die Line hat dich erwischt. Nächstes Mal besser hinhören.",
  cashed_out: "Clever gesichert, bevor es brenzlig wurde.",
};

export function GameOver({ status, banked, reachedLevel, onRestart }: Props) {
  const key = status === "running" ? "lost" : status;

  return (
    <section className={`gameover gameover--${key}`}>
      <h2 className="gameover__headline">{HEADLINES[key]}</h2>
      <p className="gameover__prize">{formatEuro(banked)}</p>
      <p className="gameover__sub">{SUBLINES[key]}</p>
      <p className="gameover__level">Erreichte Stufe: {reachedLevel} von 15</p>
      <button type="button" className="btn btn--primary btn--big" onClick={onRestart}>
        Nochmal spielen
      </button>
    </section>
  );
}
