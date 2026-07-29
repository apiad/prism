"""Text measurement and wrapping.

tesserax estimates text width as `len(text) * size * 0.6`, which is wrong for
every proportional font: real advances run from ~0.22em to ~0.94em. prism
measures against vendored tables instead, so a box actually fits its label.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .errors import PrismError, UnknownToken

FAMILIES: dict[str, str] = {
    "grotesque": "Arial, Helvetica, sans-serif",
    "serif": '"Times New Roman", Times, serif',
    "mono": '"Courier New", monospace',
}

WEIGHTS: tuple[int, ...] = (400, 700)

_METRICS_DIR = Path(__file__).parent / "vendor" / "metrics"


@dataclass(frozen=True)
class FontMetrics:
    family: str
    weight: int
    units_per_em: int
    default_advance: int
    advances: dict[int, int]


@lru_cache(maxsize=None)
def load_metrics(family: str, weight: int) -> FontMetrics:
    if family not in FAMILIES:
        raise UnknownToken(family, FAMILIES)
    if weight not in WEIGHTS:
        raise PrismError(
            f"unsupported font weight {weight!r} — prism supports only 400 and "
            "700, because those are the weights whose metrics are vendored"
        )
    raw = json.loads((_METRICS_DIR / f"{family}-{weight}.json").read_text())
    return FontMetrics(
        family=raw["family"],
        weight=raw["weight"],
        units_per_em=raw["units_per_em"],
        default_advance=raw["default_advance"],
        advances={int(k): v for k, v in raw["advances"].items()},
    )


def measure(
    text: str, size: float, family: str = "grotesque", weight: int = 400
) -> float:
    """Width of `text` in user units at `size`."""
    metrics = load_metrics(family, weight)
    total = sum(metrics.advances.get(ord(ch), metrics.default_advance) for ch in text)
    return total * size / metrics.units_per_em


def _break_word(
    word: str, max_width: float, size: float, family: str, weight: int
) -> list[str]:
    """Hard-break a word that cannot fit on any line."""
    pieces: list[str] = []
    current = ""
    for ch in word:
        candidate = current + ch
        if current and measure(candidate, size, family, weight) > max_width:
            pieces.append(current)
            current = ch
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def wrap(
    text: str,
    max_width: float,
    size: float,
    family: str = "grotesque",
    weight: int = 400,
) -> list[str]:
    """Greedily wrap `text` to `max_width`, honouring existing newlines."""
    lines: list[str] = []

    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = ""
        for word in words:
            candidate = f"{current} {word}" if current else word
            if measure(candidate, size, family, weight) <= max_width:
                current = candidate
                continue

            if current:
                lines.append(current)
                current = ""

            if measure(word, size, family, weight) <= max_width:
                current = word
            else:
                pieces = _break_word(word, max_width, size, family, weight)
                lines.extend(pieces[:-1])
                current = pieces[-1]

        if current:
            lines.append(current)

    return lines or [""]
