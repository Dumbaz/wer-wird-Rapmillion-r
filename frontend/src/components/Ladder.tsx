import type { LadderStep } from "../types";
import { formatEuro } from "../api";

interface Props {
  ladder: LadderStep[];
  currentLevel: number;
  status: string;
}

export function Ladder({ ladder, currentLevel, status }: Props) {
  const finished = status !== "running";

  return (
    <aside className="ladder" aria-label="Gewinnleiter">
      <h2 className="ladder__title">Gewinnleiter</h2>
      <ol className="ladder__list">
        {[...ladder].reverse().map((step) => {
          const cleared = step.level < currentLevel || (status === "won" && step.level === 15);
          const active = !finished && step.level === currentLevel;
          return (
            <li
              key={step.level}
              className={[
                "ladder__step",
                active ? "ladder__step--active" : "",
                cleared ? "ladder__step--cleared" : "",
                step.safe_haven ? "ladder__step--safe" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-current={active ? "step" : undefined}
            >
              <span className="ladder__level">{step.level}</span>
              <span className="ladder__prize">{formatEuro(step.prize)}</span>
              {step.safe_haven && (
                <span className="ladder__safe" title="Sicherheitsstufe">
                  ★
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </aside>
  );
}
