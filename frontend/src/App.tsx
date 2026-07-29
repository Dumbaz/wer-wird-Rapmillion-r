import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, api, formatEuro } from "./api";
import {
  isMuted,
  playCashOut,
  playCorrect,
  playGameOver,
  playLevelUp,
  playLifeline,
  playMillionaire,
  playSelect,
  playWrong,
  startTicking,
  stopTicking,
  toggleMute,
  unlockAudio,
} from "./audio/sfx";
import { AnswerButton, type AnswerVisual } from "./components/AnswerButton";
import { CoverReveal } from "./components/CoverReveal";
import { GameOver } from "./components/GameOver";
import { Ladder } from "./components/Ladder";
import { Lifelines } from "./components/Lifelines";
import { StartScreen } from "./components/StartScreen";
import type { AnswerResult, GameState, Lifeline } from "./types";

const SESSION_KEY = "rapquiz.session";
const SUSPENSE_MS = 1600;

type Phase = "idle" | "playing" | "suspense" | "revealed" | "finished";

export default function App() {
  const [state, setState] = useState<GameState | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [removed, setRemoved] = useState<number[]>([]);
  const [votes, setVotes] = useState<number[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [muted, setMuted] = useState(isMuted);

  const timerRef = useRef<number | null>(null);

  const clearTimer = () => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => () => {
    clearTimer();
    stopTicking();
  }, []);

  const resetQuestionUi = useCallback(() => {
    setSelected(null);
    setResult(null);
    setRemoved([]);
    setVotes(null);
  }, []);

  const applyState = useCallback(
    (next: GameState) => {
      setState(next);
      if (next.status === "running") {
        setPhase("playing");
        localStorage.setItem(SESSION_KEY, next.session_id);
      } else {
        setPhase("finished");
        localStorage.removeItem(SESSION_KEY);
      }
    },
    [],
  );

  const handleError = useCallback((err: unknown) => {
    stopTicking();
    if (err instanceof ApiError) {
      setError(err.message);
      if (err.status === 404) {
        localStorage.removeItem(SESSION_KEY);
        setState(null);
        setPhase("idle");
      }
    } else {
      setError("Unerwarteter Fehler.");
    }
  }, []);

  // Laufende Session nach Reload wiederherstellen
  useEffect(() => {
    const saved = localStorage.getItem(SESSION_KEY);
    if (!saved) return;
    api
      .getGame(saved)
      .then(applyState)
      .catch(() => localStorage.removeItem(SESSION_KEY));
  }, [applyState]);

  const startGame = useCallback(async () => {
    unlockAudio();
    setBusy(true);
    setError(null);
    resetQuestionUi();
    try {
      applyState(await api.startGame());
    } catch (err) {
      handleError(err);
    } finally {
      setBusy(false);
    }
  }, [applyState, handleError, resetQuestionUi]);

  const chooseAnswer = useCallback(
    async (index: number) => {
      if (!state || phase !== "playing" || busy) return;
      unlockAudio();
      playSelect();
      setSelected(index);
      setPhase("suspense");
      startTicking();

      try {
        const answer = await api.answer(state.session_id, index);
        clearTimer();
        timerRef.current = window.setTimeout(() => {
          stopTicking();
          setResult(answer);
          setState(answer.state);
          setPhase("revealed");

          if (!answer.correct) {
            playWrong();
          } else if (answer.state.status === "won") {
            playMillionaire();
          } else if (answer.state.question?.safe_haven || answer.state.level - 1 === 5 || answer.state.level - 1 === 10) {
            playLevelUp();
          } else {
            playCorrect();
          }
        }, SUSPENSE_MS);
      } catch (err) {
        stopTicking();
        setPhase("playing");
        setSelected(null);
        handleError(err);
      }
    },
    [busy, handleError, phase, state],
  );

  const continueAfterReveal = useCallback(() => {
    if (!result) return;
    const next = result.state;
    resetQuestionUi();
    if (next.status === "running") {
      applyState(next);
    } else {
      setState(next);
      setPhase("finished");
      localStorage.removeItem(SESSION_KEY);
      if (next.status === "lost") playGameOver();
    }
  }, [applyState, resetQuestionUi, result]);

  const useLifeline = useCallback(
    async (lifeline: Lifeline) => {
      if (!state || phase !== "playing" || busy) return;
      unlockAudio();
      setBusy(true);
      setError(null);
      try {
        const res = await api.lifeline(state.session_id, lifeline);
        playLifeline();
        if (lifeline === "fifty_fifty") {
          setRemoved((prev) => [...prev, ...res.removed_indexes]);
        } else if (lifeline === "publikum") {
          setVotes(res.audience_votes);
        } else {
          resetQuestionUi();
        }
        setState(res.state);
      } catch (err) {
        handleError(err);
      } finally {
        setBusy(false);
      }
    },
    [busy, handleError, phase, resetQuestionUi, state],
  );

  const cashOut = useCallback(async () => {
    if (!state || phase !== "playing" || busy) return;
    setBusy(true);
    try {
      const next = await api.cashOut(state.session_id);
      playCashOut();
      setState(next);
      setPhase("finished");
      localStorage.removeItem(SESSION_KEY);
    } catch (err) {
      handleError(err);
    } finally {
      setBusy(false);
    }
  }, [busy, handleError, phase, state]);

  const onToggleMute = () => {
    unlockAudio();
    setMuted(toggleMute());
  };

  const visualFor = (index: number): AnswerVisual => {
    if (removed.includes(index)) return "removed";
    if (phase === "revealed" && result) {
      if (index === result.correct_index) return "correct";
      if (index === selected) return "wrong";
      return "idle";
    }
    if (phase === "suspense" && index === selected) return "selected";
    return "idle";
  };

  const question = state?.question ?? null;
  const showGame = state !== null && phase !== "idle";
  const isFinished = phase === "finished";

  return (
    <div className="app">
      <header className="topbar">
        <span className="topbar__brand">
          Wer wird <strong>Rapmillionär</strong>
        </span>
        <div className="topbar__right">
          {state && !isFinished && (
            <span className="topbar__banked">
              Gesichert: <strong>{formatEuro(state.guaranteed)}</strong>
            </span>
          )}
          <button
            type="button"
            className="btn btn--ghost"
            onClick={onToggleMute}
            aria-pressed={muted}
            title={muted ? "Ton einschalten" : "Ton ausschalten"}
          >
            {muted ? "🔇" : "🔊"}
          </button>
        </div>
      </header>

      {error && (
        <div className="banner banner--error" role="alert">
          {error}
          <button type="button" className="banner__close" onClick={() => setError(null)}>
            ×
          </button>
        </div>
      )}

      <main className="layout">
        <section className="stage">
          {!showGame && <StartScreen onStart={startGame} loading={busy} />}

          {showGame && isFinished && state && (
            <GameOver
              status={state.status}
              banked={state.banked}
              reachedLevel={state.status === "won" ? 15 : Math.max(1, state.level - (state.status === "lost" ? 0 : 1))}
              onRestart={startGame}
            />
          )}

          {showGame && !isFinished && question && (
            <>
              <div className="question">
                <div className="question__head">
                  <span className="question__level">
                    Stufe {question.level}
                    {question.safe_haven && <span className="question__safe"> ★ Sicherheitsstufe</span>}
                  </span>
                  <span className="question__prize">{formatEuro(question.prize)}</span>
                </div>
                <blockquote className="question__line">„{question.line}“</blockquote>
                <p className="question__prompt">Von welchem Künstler stammt diese Line?</p>
              </div>

              <div className="answers">
                {question.answers.map((answer, index) => (
                  <AnswerButton
                    key={`${question.id}-${index}`}
                    index={index}
                    label={answer}
                    visual={visualFor(index)}
                    disabled={phase !== "playing" || busy}
                    votePercent={votes ? votes[index] : undefined}
                    onSelect={chooseAnswer}
                  />
                ))}
              </div>

              {phase === "revealed" && result && (
                <CoverReveal
                  reveal={result.reveal}
                  correct={result.correct}
                  onContinue={continueAfterReveal}
                  continueLabel={
                    result.state.status === "running" ? "Weiter zur nächsten Stufe" : "Ergebnis ansehen"
                  }
                />
              )}

              {phase === "playing" && state && (
                <div className="controls">
                  <Lifelines lifelines={state.lifelines} disabled={busy} onUse={useLifeline} />
                  <button
                    type="button"
                    className="btn btn--ghost"
                    onClick={cashOut}
                    disabled={busy || state.level === 1}
                    title={
                      state.level === 1
                        ? "Erst ab Stufe 2 möglich"
                        : `Aussteigen mit ${formatEuro(state.ladder[state.level - 2].prize)}`
                    }
                  >
                    Aussteigen
                  </button>
                </div>
              )}

              {phase === "suspense" && <p className="suspense">Ist das die richtige Antwort …?</p>}
            </>
          )}
        </section>

        {showGame && state && (
          <Ladder ladder={state.ladder} currentLevel={state.level} status={state.status} />
        )}
      </main>

      <footer className="footer">
        Zitate im Rahmen des Zitatrechts · Albumcover sind eigens generierte Grafiken
      </footer>
    </div>
  );
}
