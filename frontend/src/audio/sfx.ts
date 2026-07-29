/**
 * Funky Sound-Engine – komplett synthetisiert über die Web Audio API.
 * Keine Audiodateien, keine Lizenzfragen.
 */

const STORAGE_KEY = "rapquiz.muted";

let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let muted = localStorage.getItem(STORAGE_KEY) === "1";
let tickTimer: number | null = null;

function ensureContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const Ctor = window.AudioContext ?? (window as any).webkitAudioContext;
  if (!Ctor) return null;

  if (!ctx) {
    ctx = new Ctor();
    master = ctx.createGain();
    master.gain.value = muted ? 0 : 0.5;
    master.connect(ctx.destination);
  }
  if (ctx.state === "suspended") void ctx.resume();
  return ctx;
}

/** Muss aus einem User-Gesture heraus aufgerufen werden (Autoplay-Policy). */
export function unlockAudio(): void {
  ensureContext();
}

export function isMuted(): boolean {
  return muted;
}

export function toggleMute(): boolean {
  muted = !muted;
  localStorage.setItem(STORAGE_KEY, muted ? "1" : "0");
  if (master && ctx) {
    master.gain.setTargetAtTime(muted ? 0 : 0.5, ctx.currentTime, 0.02);
  }
  if (muted) stopTicking();
  return muted;
}

// --------------------------------------------------------------- Bausteine

interface ToneOptions {
  type?: OscillatorType;
  from: number;
  to?: number;
  start?: number;
  duration: number;
  gain?: number;
  filterFrom?: number;
  filterTo?: number;
  detune?: number;
}

function tone(opts: ToneOptions): void {
  const audio = ensureContext();
  if (!audio || !master) return;

  const t0 = audio.currentTime + (opts.start ?? 0);
  const dur = opts.duration;
  const peak = opts.gain ?? 0.3;

  const osc = audio.createOscillator();
  osc.type = opts.type ?? "sawtooth";
  osc.frequency.setValueAtTime(opts.from, t0);
  if (opts.to !== undefined) {
    osc.frequency.exponentialRampToValueAtTime(Math.max(1, opts.to), t0 + dur);
  }
  if (opts.detune) osc.detune.setValueAtTime(opts.detune, t0);

  const gain = audio.createGain();
  gain.gain.setValueAtTime(0.0001, t0);
  gain.gain.exponentialRampToValueAtTime(peak, t0 + Math.min(0.02, dur * 0.2));
  gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);

  let node: AudioNode = osc;
  if (opts.filterFrom !== undefined) {
    const filter = audio.createBiquadFilter();
    filter.type = "lowpass";
    filter.Q.value = 8;
    filter.frequency.setValueAtTime(opts.filterFrom, t0);
    filter.frequency.exponentialRampToValueAtTime(
      Math.max(60, opts.filterTo ?? opts.filterFrom),
      t0 + dur,
    );
    osc.connect(filter);
    node = filter;
  }

  node.connect(gain);
  gain.connect(master);
  osc.start(t0);
  osc.stop(t0 + dur + 0.05);
}

interface NoiseOptions {
  start?: number;
  duration: number;
  gain?: number;
  type?: BiquadFilterType;
  filterFrom: number;
  filterTo?: number;
}

function noise(opts: NoiseOptions): void {
  const audio = ensureContext();
  if (!audio || !master) return;

  const t0 = audio.currentTime + (opts.start ?? 0);
  const dur = opts.duration;
  const frames = Math.max(1, Math.floor(audio.sampleRate * dur));
  const buffer = audio.createBuffer(1, frames, audio.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < frames; i += 1) data[i] = Math.random() * 2 - 1;

  const source = audio.createBufferSource();
  source.buffer = buffer;

  const filter = audio.createBiquadFilter();
  filter.type = opts.type ?? "bandpass";
  filter.Q.value = 1.2;
  filter.frequency.setValueAtTime(opts.filterFrom, t0);
  filter.frequency.exponentialRampToValueAtTime(
    Math.max(60, opts.filterTo ?? opts.filterFrom),
    t0 + dur,
  );

  const gain = audio.createGain();
  gain.gain.setValueAtTime(opts.gain ?? 0.25, t0);
  gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);

  source.connect(filter);
  filter.connect(gain);
  gain.connect(master);
  source.start(t0);
  source.stop(t0 + dur + 0.02);
}

// ------------------------------------------------------------------ Sounds

/** Kurzer Klick beim Auswählen einer Antwort. */
export function playSelect(): void {
  tone({ type: "square", from: 660, to: 880, duration: 0.08, gain: 0.14 });
}

/** Hi-Hat-Tick während der Spannungsphase. */
export function playTick(): void {
  noise({ duration: 0.05, gain: 0.13, filterFrom: 7000, filterTo: 4000 });
  tone({ type: "sine", from: 180, to: 120, duration: 0.07, gain: 0.1 });
}

/** Wiederholender Tick, bis stopTicking() gerufen wird. */
export function startTicking(intervalMs = 260): void {
  stopTicking();
  playTick();
  tickTimer = window.setInterval(playTick, intervalMs);
}

export function stopTicking(): void {
  if (tickTimer !== null) {
    window.clearInterval(tickTimer);
    tickTimer = null;
  }
}

/** Funky Dur-Arpeggio + Clap bei richtiger Antwort. */
export function playCorrect(): void {
  stopTicking();
  const notes = [261.63, 329.63, 392.0, 523.25]; // C-Dur-Arpeggio
  notes.forEach((freq, i) => {
    tone({
      type: "sawtooth",
      from: freq,
      duration: 0.34,
      start: i * 0.075,
      gain: 0.22,
      filterFrom: 700,
      filterTo: 5200,
    });
  });
  // Funk-Bass
  tone({ type: "triangle", from: 130.81, to: 65.41, duration: 0.45, gain: 0.3 });
  // Clap
  noise({ start: 0.16, duration: 0.16, gain: 0.22, filterFrom: 2400, filterTo: 1100 });
}

/** Detunter Bass-Wobble + Vinyl-Scratch bei falscher Antwort. */
export function playWrong(): void {
  stopTicking();
  tone({ type: "sawtooth", from: 196, to: 58, duration: 0.85, gain: 0.3, filterFrom: 1400, filterTo: 180 });
  tone({ type: "square", from: 190, to: 55, duration: 0.85, gain: 0.16, detune: -35 });
  // Scratch
  noise({ start: 0.1, duration: 0.3, gain: 0.2, filterFrom: 900, filterTo: 5200, type: "bandpass" });
  noise({ start: 0.42, duration: 0.26, gain: 0.16, filterFrom: 5200, filterTo: 700, type: "bandpass" });
}

/** Kurze Fanfare beim Erreichen einer Sicherheitsstufe. */
export function playLevelUp(): void {
  const notes = [392.0, 523.25, 659.25, 783.99];
  notes.forEach((freq, i) => {
    tone({ type: "square", from: freq, duration: 0.22, start: i * 0.1, gain: 0.2, filterFrom: 1200, filterTo: 6000 });
  });
  noise({ start: 0.3, duration: 0.5, gain: 0.12, filterFrom: 6000, filterTo: 2000 });
}

/** Große Fanfare bei der Million. */
export function playMillionaire(): void {
  const melody = [523.25, 659.25, 783.99, 1046.5, 783.99, 1046.5, 1318.51];
  melody.forEach((freq, i) => {
    tone({ type: "sawtooth", from: freq, duration: 0.3, start: i * 0.14, gain: 0.24, filterFrom: 900, filterTo: 7000 });
    tone({ type: "triangle", from: freq / 2, duration: 0.3, start: i * 0.14, gain: 0.16 });
  });
  [0, 0.28, 0.56, 0.84, 1.12].forEach((t) =>
    noise({ start: t, duration: 0.2, gain: 0.16, filterFrom: 3000, filterTo: 1200 }),
  );
}

/** Absteigender Sad-Trombone-artiger Abschluss. */
export function playGameOver(): void {
  stopTicking();
  [311.13, 293.66, 277.18, 233.08].forEach((freq, i) => {
    tone({ type: "sawtooth", from: freq, to: freq * 0.94, duration: 0.4, start: i * 0.22, gain: 0.22, filterFrom: 1000, filterTo: 400 });
  });
}

/** Sound beim Einsatz eines Jokers. */
export function playLifeline(): void {
  tone({ type: "sine", from: 880, to: 1760, duration: 0.18, gain: 0.18 });
  tone({ type: "sine", from: 1320, to: 2640, duration: 0.22, start: 0.08, gain: 0.12 });
}

/** Kassen-Sound beim Aussteigen. */
export function playCashOut(): void {
  stopTicking();
  [1046.5, 1318.51].forEach((freq, i) =>
    tone({ type: "sine", from: freq, duration: 0.5, start: i * 0.09, gain: 0.22 }),
  );
  tone({ type: "triangle", from: 130.81, duration: 0.6, gain: 0.2 });
}
