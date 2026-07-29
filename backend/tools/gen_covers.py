"""Generiert deterministische Platzhalter-Albumcover als SVG.

Die Cover landen ausschliesslich in backend/static/covers/ - ein Unterordner,
der nichts anderes enthaelt.

Aufruf:  python -m tools.gen_covers      (aus dem Ordner backend/)
         python tools/gen_covers.py
"""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.data.questions import QUESTIONS  # noqa: E402

COVERS_DIR = BACKEND_DIR / "static" / "covers"
SIZE = 600

PALETTES: list[tuple[str, str, str]] = [
    ("#ff2e88", "#7b2ff7", "#00f0ff"),
    ("#00f0ff", "#0b3d91", "#ff2e88"),
    ("#ffd200", "#ff5f00", "#2b0a3d"),
    ("#00ff9d", "#005f56", "#f7ff00"),
    ("#ff004d", "#3a0a2e", "#ffb800"),
    ("#8f00ff", "#ff00c8", "#00ffe0"),
    ("#ff6a00", "#c2185b", "#ffe600"),
    ("#00c2ff", "#7a00cc", "#fffb00"),
]


class Rng:
    """Deterministischer PRNG aus einem Hash-Seed (kein globaler State)."""

    def __init__(self, seed: str) -> None:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        self.state = int.from_bytes(digest[:8], "big") or 1

    def next(self) -> int:
        # xorshift64
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
        x ^= x >> 7
        x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
        self.state = x
        return x

    def rand(self) -> float:
        return (self.next() >> 11) / float(1 << 53)

    def between(self, lo: float, hi: float) -> float:
        return lo + self.rand() * (hi - lo)

    def pick(self, seq):
        return seq[self.next() % len(seq)]


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def wrap(text: str, max_chars: int, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines or [text[:max_chars]]


def geometry(rng: Rng, mode: int, accent: str) -> str:
    parts: list[str] = []
    if mode == 0:  # Kreise
        for _ in range(7):
            cx = rng.between(0, SIZE)
            cy = rng.between(0, SIZE)
            r = rng.between(40, 210)
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                f'fill="none" stroke="{accent}" stroke-width="{rng.between(2, 9):.1f}" '
                f'opacity="{rng.between(0.15, 0.55):.2f}"/>'
            )
    elif mode == 1:  # Diagonale Baender
        for i in range(9):
            x = -SIZE + i * (SIZE / 4)
            w = rng.between(14, 55)
            parts.append(
                f'<rect x="{x:.1f}" y="-{SIZE}" width="{w:.1f}" height="{SIZE * 3}" '
                f'fill="{accent}" opacity="{rng.between(0.10, 0.40):.2f}" '
                f'transform="rotate(28 {SIZE / 2} {SIZE / 2})"/>'
            )
    elif mode == 2:  # Dreiecke
        for _ in range(6):
            cx = rng.between(0, SIZE)
            cy = rng.between(0, SIZE)
            r = rng.between(60, 200)
            pts = " ".join(
                f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}"
                for a in (rng.between(0, 6.28) + k * 2.094 for k in range(3))
            )
            parts.append(
                f'<polygon points="{pts}" fill="none" stroke="{accent}" '
                f'stroke-width="{rng.between(2, 7):.1f}" '
                f'opacity="{rng.between(0.18, 0.5):.2f}"/>'
            )
    else:  # Raster
        step = SIZE / 12
        for i in range(13):
            op = rng.between(0.08, 0.3)
            parts.append(
                f'<line x1="{i * step:.1f}" y1="0" x2="{i * step:.1f}" y2="{SIZE}" '
                f'stroke="{accent}" stroke-width="2" opacity="{op:.2f}"/>'
            )
            parts.append(
                f'<line x1="0" y1="{i * step:.1f}" x2="{SIZE}" y2="{i * step:.1f}" '
                f'stroke="{accent}" stroke-width="2" opacity="{op:.2f}"/>'
            )
    return "\n    ".join(parts)


def luminance(hex_color: str) -> float:
    """Wahrgenommene Helligkeit 0..1 (ITU-R BT.601)."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def readable_on_black(hex_color: str, fallback: str) -> str:
    """Sorgt fuer ausreichenden Kontrast auf dem schwarzen Textbalken."""
    if luminance(hex_color) >= 0.35:
        return hex_color
    return fallback if luminance(fallback) >= 0.35 else "#ffffff"


def fit_artist(artist: str) -> tuple[str, int, int]:
    """Waehlt Schriftgroesse und Laufweite so, dass der Artist nicht in die
    Jahreszahl laeuft. Gibt (Text, font_size, letter_spacing) zurueck."""
    text = artist.upper()
    available = SIZE - 52 - 52 - 78  # linker/rechter Rand + Platz fuer das Jahr
    for size, spacing in ((26, 6), (23, 4), (20, 3), (17, 2), (15, 1)):
        if len(text) * (size * 0.62 + spacing) <= available:
            return text, size, spacing
    # Notfall: kuerzen
    size, spacing = 15, 1
    max_chars = int(available / (size * 0.62 + spacing))
    return text[: max(1, max_chars - 1)] + "\u2026", size, spacing


def build_svg(artist: str, album: str, year: int) -> str:
    rng = Rng(f"{artist}|{album}")
    c1, c2, accent = rng.pick(PALETTES)
    text_accent = readable_on_black(accent, c1)
    angle = rng.between(0, 360)
    mode = rng.next() % 4

    album_lines = wrap(album.upper(), 16, 3)
    artist_line, artist_size, artist_spacing = fit_artist(artist)

    album_svg = "\n      ".join(
        f'<tspan x="52" dy="{0 if i == 0 else 58}">{esc(line)}</tspan>'
        for i, line in enumerate(album_lines)
    )
    # Textblock von unten aufbauen, Balken waechst mit der Zeilenzahl mit
    album_block_height = 58 * (len(album_lines) - 1)
    album_y = SIZE - 62 - album_block_height
    artist_y = album_y - 54
    band_top = artist_y - 46
    band_height = SIZE - band_top

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}" role="img" aria-label="{esc(album)} von {esc(artist)}">
  <defs>
    <linearGradient id="bg" gradientTransform="rotate({angle:.0f} 0.5 0.5)">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
    <clipPath id="clip"><rect width="{SIZE}" height="{SIZE}"/></clipPath>
  </defs>
  <g clip-path="url(#clip)">
    <rect width="{SIZE}" height="{SIZE}" fill="url(#bg)"/>
    {geometry(rng, mode, accent)}
    <rect width="{SIZE}" height="{SIZE}" filter="url(#grain)" opacity="0.10"/>
    <rect x="0" y="{band_top}" width="{SIZE}" height="{band_height}" fill="#000" opacity="0.58"/>
    <text x="52" y="{artist_y}" font-family="Helvetica, Arial, sans-serif" font-size="{artist_size}" font-weight="700" letter-spacing="{artist_spacing}" fill="{text_accent}">{esc(artist_line)}</text>
    <text x="52" y="{album_y}" font-family="Helvetica, Arial, sans-serif" font-size="50" font-weight="800" letter-spacing="1" fill="#ffffff">
      {album_svg}
    </text>
    <text x="{SIZE - 52}" y="{artist_y}" text-anchor="end" font-family="Helvetica, Arial, sans-serif" font-size="26" font-weight="700" fill="#ffffff" opacity="0.75">{year}</text>
  </g>
  <rect x="4" y="4" width="{SIZE - 8}" height="{SIZE - 8}" fill="none" stroke="{accent}" stroke-width="6" opacity="0.9"/>
</svg>
"""


def main() -> int:
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    seen: dict[str, str] = {}
    written = 0

    for question in QUESTIONS:
        if question.cover in seen:
            continue
        seen[question.cover] = question.album
        path = COVERS_DIR / question.cover
        path.write_text(
            build_svg(question.artist, question.album, question.year),
            encoding="utf-8",
        )
        written += 1

    # Verwaiste Dateien entfernen, damit der Ordner sauber bleibt
    removed = 0
    for existing in COVERS_DIR.glob("*.svg"):
        if existing.name not in seen:
            existing.unlink()
            removed += 1

    print(f"{written} Cover geschrieben, {removed} verwaiste entfernt -> {COVERS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
