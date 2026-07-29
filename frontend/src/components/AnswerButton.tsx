const LETTERS = ["A", "B", "C"];

export type AnswerVisual = "idle" | "selected" | "correct" | "wrong" | "removed";

interface Props {
  index: number;
  label: string;
  visual: AnswerVisual;
  disabled: boolean;
  votePercent?: number;
  onSelect: (index: number) => void;
}

export function AnswerButton({
  index,
  label,
  visual,
  disabled,
  votePercent,
  onSelect,
}: Props) {
  const removed = visual === "removed";

  return (
    <button
      type="button"
      className={`answer answer--${visual}`}
      disabled={disabled || removed}
      onClick={() => onSelect(index)}
      aria-label={`Antwort ${LETTERS[index]}: ${label}`}
    >
      <span className="answer__letter">{LETTERS[index]}</span>
      <span className="answer__label">{removed ? "" : label}</span>
      {votePercent !== undefined && !removed && (
        <span className="answer__vote">
          <span className="answer__vote-bar" style={{ width: `${votePercent}%` }} />
          <span className="answer__vote-value">{votePercent}%</span>
        </span>
      )}
    </button>
  );
}
