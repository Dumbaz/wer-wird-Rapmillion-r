interface Props {
  onStart: () => void;
  loading: boolean;
}

export function StartScreen({ onStart, loading }: Props) {
  return (
    <section className="start">
      <p className="start__kicker">Das Deutschrap-Quiz</p>
      <h1 className="start__title">
        Wer wird <span className="start__title-accent">Rapmillionär</span>
      </h1>
      <p className="start__text">
        15 Stufen. 15 Lines. Von Chart-Hits bis Underground-Klassiker aus 1991.
        Erkenne den Künstler hinter der Zeile und arbeite dich bis zur Million hoch.
      </p>
      <ul className="start__rules">
        <li>3 Antworten pro Frage – nur eine ist richtig</li>
        <li>Sicherheitsstufen bei 500 € und 16.000 €</li>
        <li>3 Joker: Fifty-Fifty, Publikum, Skip</li>
        <li>Jederzeit aussteigen und den Gewinn sichern</li>
      </ul>
      <button
        type="button"
        className="btn btn--primary btn--big"
        onClick={onStart}
        disabled={loading}
      >
        {loading ? "Lädt …" : "Spiel starten"}
      </button>
    </section>
  );
}
