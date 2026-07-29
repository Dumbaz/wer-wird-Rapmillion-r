import type { LifelineState, Lifeline } from "../types";

const LABELS: Record<Lifeline, { icon: string; name: string; hint: string }> = {
  fifty_fifty: { icon: "50:50", name: "Fifty-Fifty", hint: "Eine falsche Antwort verschwindet" },
  publikum: { icon: "◍", name: "Publikum", hint: "Das Publikum stimmt ab" },
  skip: { icon: "⤳", name: "Skip", hint: "Neue Frage auf gleicher Stufe" },
};

interface Props {
  lifelines: LifelineState;
  disabled: boolean;
  onUse: (lifeline: Lifeline) => void;
}

export function Lifelines({ lifelines, disabled, onUse }: Props) {
  return (
    <div className="lifelines" role="group" aria-label="Joker">
      {(Object.keys(LABELS) as Lifeline[]).map((key) => {
        const available = lifelines[key];
        const meta = LABELS[key];
        return (
          <button
            key={key}
            type="button"
            className={`lifeline ${available ? "" : "lifeline--used"}`}
            disabled={!available || disabled}
            onClick={() => onUse(key)}
            title={available ? meta.hint : "Bereits verbraucht"}
          >
            <span className="lifeline__icon">{meta.icon}</span>
            <span className="lifeline__name">{meta.name}</span>
          </button>
        );
      })}
    </div>
  );
}
