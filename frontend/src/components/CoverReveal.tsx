import type { SongReveal } from "../types";

interface Props {
  reveal: SongReveal;
  correct: boolean;
  onContinue: () => void;
  continueLabel: string;
}

export function CoverReveal({ reveal, correct, onContinue, continueLabel }: Props) {
  return (
    <div className={`reveal ${correct ? "reveal--correct" : "reveal--wrong"}`} role="status">
      <img
        className="reveal__cover"
        src={reveal.cover_url}
        alt={`Albumcover: ${reveal.album} von ${reveal.artist}`}
        width={180}
        height={180}
      />
      <div className="reveal__meta">
        <p className="reveal__verdict">{correct ? "Richtig!" : "Leider falsch"}</p>
        <h3 className="reveal__artist">{reveal.artist}</h3>
        <p className="reveal__track">
          „{reveal.track}“ · <em>{reveal.album}</em> ({reveal.year})
        </p>
        <p className="reveal__fact">{reveal.fun_fact}</p>
        <button type="button" className="btn btn--primary" onClick={onContinue} autoFocus>
          {continueLabel}
        </button>
      </div>
    </div>
  );
}
