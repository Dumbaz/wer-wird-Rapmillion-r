import { formatEuro } from "../api";

interface Props {
  onStart: () => void;
  loading: boolean;
  /** Stufe einer noch laufenden Runde, sonst null. */
  resumeLevel: number | null;
  /** Preisgeld der Stufe, auf der die laufende Runde steht. */
  resumePrize: number;
  onResume: () => void;
}

export function StartScreen({
  onStart,
  loading,
  resumeLevel,
  resumePrize,
  onResume,
}: Props) {
  return (
    <section className="start">
      <p className="start__kicker">Das Deutschrap-Quiz</p>
      <h1 className="start__title">
        Wer wird <span className="start__title-accent">Rapmillionär</span>
      </h1>
      <p className="start__text">
        15 Stufen. 15 Lines. Von Chart-Hits über Berliner Battle Rap bis in den
        Untergrund. Erkenne den Künstler hinter der Zeile und arbeite dich bis
        zur Million hoch.
      </p>
      <ul className="start__rules">
        <li>3 Antworten pro Frage – nur eine ist richtig</li>
        <li>Sicherheitsstufen bei 500 € und 16.000 €</li>
        <li>3 Joker: Fifty-Fifty, Publikum, Skip</li>
        <li>Jederzeit aussteigen und den Gewinn sichern</li>
      </ul>

      <div className="start__actions">
        <button
          type="button"
          className="btn btn--primary btn--big"
          onClick={onStart}
          disabled={loading}
        >
          {loading ? "Lädt …" : resumeLevel ? "Neue Runde starten" : "Spiel starten"}
        </button>

        {resumeLevel !== null && (
          <button type="button" className="btn btn--big" onClick={onResume} disabled={loading}>
            Runde fortsetzen – Stufe {resumeLevel} ({formatEuro(resumePrize)})
          </button>
        )}
      </div>
    </section>
  );
}
