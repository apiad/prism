# prism VS1 — `flow` End-to-End Implementation Plan

**Status:** Implemented — all 13 tasks landed in v0.1.0 (`dcc1576`). The
follow-up slices this plan deferred (the other nine archetypes, the `dark` /
`paper` / `mono` themes, `SKILL.md`, the docs site) also shipped in the same
release, so the "deliberately leaves out" list below is historical.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a YAML `type: flow` spec into a themed, typographically-correct SVG diagram through the complete prism stack — envelope, registry, theme, typography, icons, archetype, framing, public API and CLI.

**Architecture:** A YAML spec is loaded by `envelope.py`, dispatched through `registry.py` to the `flow` archetype, which validates a pydantic model and composes tesserax shapes into a `Group`. `frame.py` wraps that body with title/caption and accessibility metadata into a `Canvas`, fits it, and emits SVG. All text is measured against vendored font metrics so every box actually contains its label.

**Tech Stack:** Python 3.12+, tesserax (SVG + layout), pydantic v2 (validation + JSON Schema), PyYAML, pytest, ruff. fontTools and the Liberation font files are **build-time only** — used by a script to extract metrics, never imported at runtime.

## Global Constraints

- `requires-python = ">=3.12"`.
- Runtime dependencies are exactly: `tesserax`, `pyyaml`, `pydantic>=2`. Nothing else. Optional extra `export` adds `tesserax[export]`.
- Distribution name is `prism-svg`; import name is `prism`.
- Licence MIT. Vendored Lucide keeps its ISC notice at `prism/vendor/lucide/LICENSE`.
- Font families are exactly `grotesque` / `serif` / `mono`. Font weights are exactly `400` and `700` — no other value is valid anywhere.
- All code, comments, identifiers, error strings, CLI help and commit messages in **English**.
- Every archetype reads theme **tokens** only. A literal colour or font size anywhere in `prism/archetypes/` is a bug.
- Rendering is deterministic: identical input produces byte-identical output.
- Commit after every task. Conventional commits. Work directly on `main`.

---

### Task 1: Repo scaffold

**Files:**
- Create: `pyproject.toml`, `prism/__init__.py`, `prism/py.typed`, `tests/test_package.py`, `LICENSE`, `README.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `prism.__version__: str`.

- [x] **Step 1: Write the failing test**

```python
# tests/test_package.py
import prism


def test_package_exposes_version():
    assert isinstance(prism.__version__, str)
    assert prism.__version__ == "0.1.0.dev0"
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_package.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism'`

- [x] **Step 3: Write minimal implementation**

```toml
# pyproject.toml
[project]
name = "prism-svg"
version = "0.1.0.dev0"
description = "Declarative YAML to SVG diagrams"
readme = "README.md"
requires-python = ">=3.12"
license = "MIT"
authors = [{ name = "Alejandro Piad", email = "alepiad@gmail.com" }]
dependencies = ["tesserax>=0.12", "pyyaml>=6.0", "pydantic>=2.0"]

[project.optional-dependencies]
export = ["tesserax[export]>=0.12"]

[project.scripts]
prism = "prism.cli:main"

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.6", "fonttools>=4.53"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["prism"]

[tool.ruff]
line-length = 88
```

```python
# prism/__init__.py
"""Declarative YAML to SVG diagrams."""

__version__ = "0.1.0.dev0"
```

Create an empty `prism/py.typed`. Write `LICENSE` as the standard MIT text, copyright `2026 Alejandro Piad`. Write a `README.md` with a one-paragraph description; it gets its real content in Task 13.

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_package.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add pyproject.toml prism/ tests/ LICENSE README.md
git commit -m "chore: scaffold prism-svg package"
```

---

### Task 2: Agent-legible errors

**Files:**
- Create: `prism/errors.py`, `tests/test_errors.py`

**Interfaces:**
- Produces: `PrismError`, `SpecError`, `UnknownArchetype`, `UnknownIcon`, `UnknownToken`, and `suggest(value: str, candidates: Iterable[str], n: int = 3) -> list[str]`.

Every downstream task raises these rather than bare `ValueError`. The message format matters: an agent's recovery loop is only as good as the error string.

- [x] **Step 1: Write the failing test**

```python
# tests/test_errors.py
import pytest

from prism.errors import PrismError, UnknownIcon, suggest


def test_suggest_ranks_close_matches_first():
    assert suggest("databse", ["database", "data-flow", "shield"])[0] == "database"


def test_suggest_returns_empty_when_nothing_is_close():
    assert suggest("zzzzzz", ["database", "shield"]) == []


def test_unknown_icon_message_names_value_and_suggestions():
    err = UnknownIcon("databse", ["database", "shield"])
    message = str(err)
    assert "databse" in message
    assert "database" in message
    assert isinstance(err, PrismError)


def test_unknown_icon_message_survives_no_suggestions():
    message = str(UnknownIcon("zzzzzz", ["database", "shield"]))
    assert "zzzzzz" in message
    assert "2 known icons" in message


def test_prism_error_is_catchable_as_exception():
    with pytest.raises(PrismError):
        raise UnknownIcon("x", ["database"])
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.errors'`

- [x] **Step 3: Write minimal implementation**

```python
# prism/errors.py
"""Exceptions written to be read by a model, not only by a human."""

from __future__ import annotations

import difflib
from collections.abc import Iterable


def suggest(value: str, candidates: Iterable[str], n: int = 3) -> list[str]:
    """Return the closest candidates to `value`, best first."""
    return difflib.get_close_matches(value, list(candidates), n=n, cutoff=0.6)


class PrismError(Exception):
    """Base class for every error prism raises on purpose."""


class SpecError(PrismError):
    """The spec failed validation against its archetype's schema."""


class _UnknownName(PrismError):
    noun = "value"

    def __init__(self, value: str, candidates: Iterable[str]) -> None:
        known = list(candidates)
        hits = suggest(value, known)
        if hits:
            tail = f"did you mean: {', '.join(hits)}?"
        else:
            tail = f"no close match among {len(known)} known {self.noun}s"
        super().__init__(f"unknown {self.noun} {value!r} — {tail}")
        self.value = value
        self.candidates = known


class UnknownArchetype(_UnknownName):
    noun = "archetype"


class UnknownIcon(_UnknownName):
    noun = "icon"


class UnknownToken(_UnknownName):
    noun = "token"
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_errors.py -v`
Expected: PASS (5 tests)

- [x] **Step 5: Commit**

```bash
git add prism/errors.py tests/test_errors.py
git commit -m "feat(errors): agent-legible exceptions with did-you-mean"
```

---

### Task 3: Extract and vendor font metrics

**Files:**
- Create: `scripts/build_metrics.py`, `prism/vendor/metrics/grotesque-400.json`, `prism/vendor/metrics/grotesque-700.json`, `prism/vendor/metrics/serif-400.json`, `prism/vendor/metrics/serif-700.json`, `prism/vendor/metrics/mono-400.json`, `prism/vendor/metrics/mono-700.json`, `tests/test_metrics_data.py`

**Interfaces:**
- Produces: six JSON files, each `{"family": str, "weight": int, "units_per_em": int, "default_advance": int, "advances": {"<codepoint>": int}}`.

The Liberation faces are metric-compatible with Arial, Times New Roman and Courier New, which is exactly why those three stacks were chosen. The script is run once by a developer; `fonttools` never ships as a runtime dependency.

- [x] **Step 1: Write the failing test**

```python
# tests/test_metrics_data.py
import json
from pathlib import Path

import pytest

METRICS_DIR = Path(__file__).parent.parent / "prism" / "vendor" / "metrics"
EXPECTED = [
    "grotesque-400",
    "grotesque-700",
    "serif-400",
    "serif-700",
    "mono-400",
    "mono-700",
]


@pytest.mark.parametrize("stem", EXPECTED)
def test_metrics_file_is_well_formed(stem):
    data = json.loads((METRICS_DIR / f"{stem}.json").read_text())
    family, weight = stem.rsplit("-", 1)
    assert data["family"] == family
    assert data["weight"] == int(weight)
    assert data["units_per_em"] > 0
    assert data["default_advance"] > 0
    # ASCII printable range must be fully covered.
    for codepoint in range(32, 127):
        assert str(codepoint) in data["advances"]


def test_proportional_font_has_varying_advances():
    data = json.loads((METRICS_DIR / "grotesque-400.json").read_text())
    assert data["advances"][str(ord("i"))] < data["advances"][str(ord("W"))]


def test_mono_font_has_uniform_advances():
    data = json.loads((METRICS_DIR / "mono-400.json").read_text())
    assert data["advances"][str(ord("i"))] == data["advances"][str(ord("W"))]
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_metrics_data.py -v`
Expected: FAIL — `FileNotFoundError` for `grotesque-400.json`

- [x] **Step 3: Write minimal implementation**

```python
# scripts/build_metrics.py
"""Extract advance-width tables from the Liberation faces into vendored JSON.

Run once by a developer, never at runtime:

    uv run python scripts/build_metrics.py

The Liberation faces are metric-compatible with Arial, Times New Roman and
Courier New, so the tables hold on Linux, macOS and Windows alike.
"""

from __future__ import annotations

import json
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
FACES = {
    ("grotesque", 400): "LiberationSans-Regular.ttf",
    ("grotesque", 700): "LiberationSans-Bold.ttf",
    ("serif", 400): "LiberationSerif-Regular.ttf",
    ("serif", 700): "LiberationSerif-Bold.ttf",
    ("mono", 400): "LiberationMono-Regular.ttf",
    ("mono", 700): "LiberationMono-Bold.ttf",
}

# ASCII printable, Latin-1 supplement, and the punctuation real prose uses.
CODEPOINTS = (
    list(range(32, 127))
    + list(range(160, 256))
    + [0x2010, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026, 0x20AC]
)

OUT_DIR = Path(__file__).parent.parent / "prism" / "vendor" / "metrics"


def extract(path: Path, family: str, weight: int) -> dict:
    font = TTFont(path)
    units_per_em = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    advances: dict[str, int] = {}
    for codepoint in CODEPOINTS:
        glyph = cmap.get(codepoint)
        if glyph is None:
            continue
        advances[str(codepoint)] = hmtx[glyph][0]

    # Fall back to '?' — a mid-width glyph present in every face.
    default_advance = advances[str(ord("?"))]

    return {
        "family": family,
        "weight": weight,
        "units_per_em": units_per_em,
        "default_advance": default_advance,
        "advances": advances,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for (family, weight), filename in FACES.items():
        path = FONT_DIR / filename
        if not path.exists():
            raise SystemExit(
                f"missing {path}. Install the Liberation fonts "
                "(Debian/Ubuntu: apt install fonts-liberation)."
            )
        data = extract(path, family, weight)
        out = OUT_DIR / f"{family}-{weight}.json"
        out.write_text(json.dumps(data, indent=0, sort_keys=True) + "\n")
        print(f"wrote {out} ({len(data['advances'])} glyphs)")


if __name__ == "__main__":
    main()
```

Then run it:

```bash
uv run python scripts/build_metrics.py
```

Add to `pyproject.toml` under `[tool.hatch.build.targets.wheel]` so the data ships in the wheel:

```toml
[tool.hatch.build.targets.wheel.force-include]
"prism/vendor" = "prism/vendor"
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_metrics_data.py -v`
Expected: PASS (8 tests)

- [x] **Step 5: Commit**

```bash
git add scripts/build_metrics.py prism/vendor/metrics/ tests/test_metrics_data.py pyproject.toml
git commit -m "feat(typography): vendor Liberation-derived advance-width tables"
```

---

### Task 4: Measure text

**Files:**
- Create: `prism/typography.py`, `tests/test_typography_measure.py`

**Interfaces:**
- Consumes: the JSON files from Task 3.
- Produces:
  - `FAMILIES: dict[str, str]` mapping family token to CSS stack.
  - `FontMetrics` frozen dataclass with `family`, `weight`, `units_per_em`, `default_advance`, `advances: dict[int, int]`.
  - `load_metrics(family: str, weight: int) -> FontMetrics` (cached).
  - `measure(text: str, size: float, family: str = "grotesque", weight: int = 400) -> float`.

- [x] **Step 1: Write the failing test**

```python
# tests/test_typography_measure.py
import pytest

from prism.errors import PrismError
from prism.typography import FAMILIES, load_metrics, measure


def test_families_are_exactly_the_three_supported_stacks():
    assert set(FAMILIES) == {"grotesque", "serif", "mono"}
    assert "Arial" in FAMILIES["grotesque"]


def test_empty_string_measures_zero():
    assert measure("", 12) == 0.0


def test_measure_scales_linearly_with_size():
    assert measure("Ingest", 24) == pytest.approx(measure("Ingest", 12) * 2)


def test_narrow_text_measures_less_than_wide_text():
    assert measure("lllll", 12) < measure("WWWWW", 12)


def test_mono_measures_purely_by_length():
    five = measure("iiiii", 12, family="mono")
    assert measure("WWWWW", 12, family="mono") == pytest.approx(five)


def test_bold_is_wider_than_regular_for_the_same_string():
    assert measure("Ingest", 12, weight=700) > measure("Ingest", 12, weight=400)


def test_unknown_glyph_falls_back_to_default_advance():
    metrics = load_metrics("grotesque", 400)
    expected = metrics.default_advance * 12 / metrics.units_per_em
    assert measure("中", 12) == pytest.approx(expected)


def test_unknown_family_raises_prism_error():
    with pytest.raises(PrismError):
        measure("x", 12, family="comic")


def test_unknown_weight_raises_prism_error():
    with pytest.raises(PrismError):
        measure("x", 12, weight=600)
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_typography_measure.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.typography'`

- [x] **Step 3: Write minimal implementation**

```python
# prism/typography.py
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
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_typography_measure.py -v`
Expected: PASS (9 tests)

- [x] **Step 5: Commit**

```bash
git add prism/typography.py tests/test_typography_measure.py
git commit -m "feat(typography): measure text against vendored metrics"
```

---

### Task 5: Wrap text

**Files:**
- Modify: `prism/typography.py`
- Create: `tests/test_typography_wrap.py`

**Interfaces:**
- Produces: `wrap(text: str, max_width: float, size: float, family: str = "grotesque", weight: int = 400) -> list[str]`.

- [x] **Step 1: Write the failing test**

```python
# tests/test_typography_wrap.py
from prism.typography import measure, wrap


def test_short_text_stays_on_one_line():
    assert wrap("Ingest", 500, 12) == ["Ingest"]


def test_empty_text_yields_a_single_empty_line():
    assert wrap("", 500, 12) == [""]


def test_text_breaks_at_whitespace():
    lines = wrap("Ingest raw events from the bus", 80, 12)
    assert len(lines) > 1
    assert all(" " not in line[:1] for line in lines)


def test_no_wrapped_line_exceeds_the_budget():
    budget = 80
    for line in wrap("Ingest raw events from the upstream bus", budget, 12):
        assert measure(line, 12) <= budget


def test_a_single_oversized_word_is_hard_broken():
    lines = wrap("Supercalifragilisticexpialidocious", 40, 12)
    assert len(lines) > 1
    for line in lines:
        assert measure(line, 12) <= 40


def test_existing_newlines_are_honoured_as_hard_breaks():
    assert wrap("Ingest\nVerify", 500, 12) == ["Ingest", "Verify"]


def test_runs_of_whitespace_collapse():
    assert wrap("Ingest    events", 500, 12) == ["Ingest events"]
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_typography_wrap.py -v`
Expected: FAIL — `ImportError: cannot import name 'wrap'`

- [x] **Step 3: Write minimal implementation**

Append to `prism/typography.py`:

```python
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
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_typography_wrap.py -v`
Expected: PASS (7 tests)

- [x] **Step 5: Commit**

```bash
git add prism/typography.py tests/test_typography_wrap.py
git commit -m "feat(typography): greedy word-wrap with hard-break fallback"
```

---

### Task 6: `MeasuredText` and `TextBlock`

**Files:**
- Create: `prism/text.py`, `tests/test_text.py`

**Interfaces:**
- Consumes: `measure`, `wrap`, `FAMILIES` from `prism.typography`.
- Produces:
  - `MeasuredText(content, size, family="grotesque", weight=400, fill=..., anchor="middle", baseline="middle")` — a `tesserax.Text` subclass whose `local()` returns true bounds and whose SVG carries `font-weight`.
  - `TextBlock(text, max_width, size, family="grotesque", weight=400, fill=..., line_height=1.35, anchor="middle")` — a `tesserax.Group` of `MeasuredText` lines stacked by `ColumnLayout`.

This is the component that makes tesserax's layout engines correct for us: they consume `Bounds`, and we hand them true ones.

- [x] **Step 1: Write the failing test**

```python
# tests/test_text.py
from tesserax.color import hex as parse_hex

from prism.text import MeasuredText, TextBlock
from prism.typography import measure

INK = parse_hex("#111827")


def test_measured_text_bounds_match_measured_width():
    text = MeasuredText("Ingest", size=13, fill=INK)
    assert text.local().width == measure("Ingest", 13)


def test_measured_text_bounds_beat_the_tesserax_heuristic():
    # tesserax would give len * size * 0.6 == 5 * 12 * 0.6 == 36 for both.
    narrow = MeasuredText("lllll", size=12, fill=INK).local().width
    wide = MeasuredText("WWWWW", size=12, fill=INK).local().width
    assert narrow != wide


def test_measured_text_height_is_the_font_size():
    assert MeasuredText("Ingest", size=13, fill=INK).local().height == 13


def test_measured_text_emits_font_weight_and_family():
    svg = MeasuredText("Ingest", size=13, weight=700, fill=INK).render()
    assert 'font-weight="700"' in svg
    assert "Arial" in svg


def test_measured_text_escapes_markup_in_content():
    svg = MeasuredText("a<b & c", size=12, fill=INK).render()
    assert "&lt;b" in svg
    assert "&amp;" in svg


def test_text_block_splits_into_lines():
    block = TextBlock("Ingest raw events from the bus", 80, size=12, fill=INK)
    assert len(block.lines) > 1
    assert len(block.shapes) == len(block.lines)


def test_text_block_width_never_exceeds_its_budget():
    block = TextBlock("Ingest raw events from the bus", 80, size=12, fill=INK)
    assert block.local().width <= 80


def test_text_block_height_grows_with_line_count():
    one = TextBlock("Ingest", 500, size=12, fill=INK).local().height
    many = TextBlock("Ingest raw events from the bus", 80, size=12, fill=INK)
    assert many.local().height > one
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_text.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.text'`

- [x] **Step 3: Write minimal implementation**

```python
# prism/text.py
"""Text shapes that know how wide they really are."""

from __future__ import annotations

from typing import Literal
from xml.sax.saxutils import escape, quoteattr

from tesserax import Text
from tesserax.color import Color
from tesserax.core import Bounds
from tesserax.layout import ColumnLayout

from .typography import FAMILIES, measure, wrap


class MeasuredText(Text):
    """A tesserax Text whose bounds come from real font metrics."""

    def __init__(
        self,
        content: str,
        size: float,
        fill: Color,
        family: str = "grotesque",
        weight: int = 400,
        anchor: Literal["start", "middle", "end"] = "middle",
        baseline: Literal["top", "middle", "bottom"] = "middle",
    ) -> None:
        super().__init__(
            content,
            size=size,
            font=FAMILIES[family],
            anchor=anchor,
            baseline=baseline,
            fill=fill,
        )
        self.family = family
        self.weight = weight

    def local(self) -> Bounds:
        width = measure(self.content, self.size, self.family, self.weight)
        height = self.size
        if self._anchor == "middle":
            return Bounds(-width / 2, -height / 2, width, height)
        if self._anchor == "end":
            return Bounds(-width, -height / 2, width, height)
        return Bounds(0, -height / 2, width, height)

    def _render(self) -> str:
        return (
            f'<text x="0" y="0" font-family={quoteattr(self.font)} '
            f'font-size="{self.size}" font-weight="{self.weight}" '
            f'fill="{self.fill}" text-anchor="{self._anchor}" '
            f'dominant-baseline="{self._baseline}">'
            f"{escape(self.content)}</text>"
        )


class TextBlock(ColumnLayout):
    """A wrapped, multi-line run of text with exact bounds."""

    def __init__(
        self,
        text: str,
        max_width: float,
        size: float,
        fill: Color,
        family: str = "grotesque",
        weight: int = 400,
        line_height: float = 1.35,
        anchor: Literal["start", "middle", "end"] = "middle",
    ) -> None:
        self.lines = wrap(text, max_width, size, family, weight)
        align = {"start": "start", "middle": "middle", "end": "end"}[anchor]
        super().__init__(
            [
                MeasuredText(
                    line,
                    size=size,
                    fill=fill,
                    family=family,
                    weight=weight,
                    anchor=anchor,
                )
                for line in self.lines
            ],
            align=align,
            gap=size * (line_height - 1),
        )
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_text.py -v`
Expected: PASS (8 tests)

(`tesserax.layout.Align` is `Literal["start", "middle", "end"]`, so the mapping above is an identity — it exists to make the anchor/align relationship explicit at the call site.)

- [x] **Step 5: Commit**

```bash
git add prism/text.py tests/test_text.py
git commit -m "feat(text): MeasuredText and TextBlock with true bounds"
```

---

### Task 7: Theme tokens

**Files:**
- Create: `prism/theme.py`, `prism/themes/default.yaml`, `tests/test_theme.py`

**Interfaces:**
- Produces:
  - `Palette`, `Typography`, `Geometry`, `Theme` (pydantic models).
  - `Theme.color(ref: int | str | None) -> Color` — resolves a ramp index, a palette token name, or `None` (→ `ink`).
  - `load_theme(ref: str = "default", overrides: dict[str, Any] | None = None) -> Theme` — `ref` is a bundled name or a path to a YAML file; `overrides` keys are dotted paths (`palette.ink`).

- [x] **Step 1: Write the failing test**

```python
# tests/test_theme.py
import pytest
from tesserax.color import hex as parse_hex

from prism.errors import PrismError
from prism.theme import Theme, load_theme


def test_default_theme_loads():
    theme = load_theme("default")
    assert isinstance(theme, Theme)
    assert theme.name == "default"
    assert len(theme.palette.ramp) >= 3


def test_color_resolves_a_ramp_index():
    theme = load_theme("default")
    assert theme.color(0) == parse_hex(theme.palette.ramp[0])


def test_ramp_index_wraps_around():
    theme = load_theme("default")
    assert theme.color(len(theme.palette.ramp)) == theme.color(0)


def test_color_resolves_a_palette_token_name():
    theme = load_theme("default")
    assert theme.color("muted") == parse_hex(theme.palette.muted)


def test_color_defaults_to_ink():
    theme = load_theme("default")
    assert theme.color(None) == parse_hex(theme.palette.ink)


def test_unknown_token_name_raises():
    theme = load_theme("default")
    with pytest.raises(PrismError):
        theme.color("accnt")


def test_dotted_overrides_apply():
    theme = load_theme("default", {"palette.ink": "#0b1020", "geometry.radius": 2})
    assert theme.palette.ink == "#0b1020"
    assert theme.geometry.radius == 2


def test_unknown_theme_name_raises():
    with pytest.raises(PrismError):
        load_theme("defualt")


def test_weight_other_than_400_or_700_is_rejected():
    with pytest.raises(PrismError):
        load_theme("default", {"typography.weight": {"label": 600}})
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_theme.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.theme'`

- [x] **Step 3: Write minimal implementation**

```yaml
# prism/themes/default.yaml
name: default
palette:
  surface: "#ffffff"
  ink: "#111827"
  muted: "#6b7280"
  line: "#d1d5db"
  ramp: ["#0f766e", "#b45309", "#4338ca", "#be123c", "#0369a1", "#65a30d"]
  ok: "#15803d"
  warn: "#b45309"
  bad: "#b91c1c"
typography:
  family: grotesque
  scale: {title: 20, subtitle: 13, label: 13, sublabel: 11, note: 10, badge: 10}
  weight: {title: 700, label: 700, sublabel: 400, note: 400, badge: 700}
  line_height: 1.35
geometry:
  radius: 6
  stroke: 1.5
  gap: 24
  pad: 12
  arrow: standard
texture: clean
```

```python
# prism/theme.py
"""Themes are data — a token set, never code."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator
from tesserax.color import Color
from tesserax.color import hex as parse_hex

from .errors import PrismError, UnknownToken
from .typography import FAMILIES, WEIGHTS

_THEMES_DIR = Path(__file__).parent / "themes"


class Palette(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface: str
    ink: str
    muted: str
    line: str
    ramp: list[str] = Field(min_length=3)
    ok: str
    warn: str
    bad: str


class Typography(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str = "grotesque"
    scale: dict[str, float]
    weight: dict[str, int]
    line_height: float = 1.35

    @field_validator("family")
    @classmethod
    def _known_family(cls, value: str) -> str:
        if value not in FAMILIES:
            raise UnknownToken(value, FAMILIES)
        return value

    @field_validator("weight")
    @classmethod
    def _supported_weights(cls, value: dict[str, int]) -> dict[str, int]:
        for role, weight in value.items():
            if weight not in WEIGHTS:
                raise PrismError(
                    f"typography.weight.{role} is {weight!r}; prism supports "
                    "only 400 and 700, the weights whose metrics are vendored"
                )
        return value


class Geometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    radius: float = 6
    stroke: float = 1.5
    gap: float = 24
    pad: float = 12
    arrow: Literal["standard", "thin", "block"] = "standard"


class Theme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    palette: Palette
    typography: Typography
    geometry: Geometry
    texture: Literal["clean", "sketch"] = "clean"

    def color(self, ref: int | str | None = None) -> Color:
        if ref is None:
            return parse_hex(self.palette.ink)
        if isinstance(ref, int):
            ramp = self.palette.ramp
            return parse_hex(ramp[ref % len(ramp)])
        named = {
            k: v for k, v in self.palette.model_dump().items() if isinstance(v, str)
        }
        if ref not in named:
            raise UnknownToken(ref, named)
        return parse_hex(named[ref])

    def size(self, role: str) -> float:
        if role not in self.typography.scale:
            raise UnknownToken(role, self.typography.scale)
        return self.typography.scale[role]

    def weight(self, role: str) -> int:
        return self.typography.weight.get(role, 400)


def _apply_overrides(data: dict[str, Any], overrides: dict[str, Any]) -> dict:
    for dotted, value in overrides.items():
        target = data
        *parents, leaf = dotted.split(".")
        for part in parents:
            if part not in target or not isinstance(target[part], dict):
                raise UnknownToken(dotted, _dotted_paths(data))
            target = target[part]
        if leaf not in target:
            raise UnknownToken(dotted, _dotted_paths(data))
        target[leaf] = value
    return data


def _dotted_paths(data: dict[str, Any], prefix: str = "") -> list[str]:
    paths: list[str] = []
    for key, value in data.items():
        path = f"{prefix}{key}"
        paths.append(path)
        if isinstance(value, dict):
            paths.extend(_dotted_paths(value, f"{path}."))
    return paths


def bundled_themes() -> list[str]:
    return sorted(p.stem for p in _THEMES_DIR.glob("*.yaml"))


def load_theme(ref: str = "default", overrides: dict[str, Any] | None = None) -> Theme:
    path = Path(ref)
    if not path.suffix:
        path = _THEMES_DIR / f"{ref}.yaml"
        if not path.exists():
            raise UnknownToken(ref, bundled_themes())
    elif not path.exists():
        raise PrismError(f"theme file not found: {ref}")

    data = yaml.safe_load(path.read_text())
    if overrides:
        data = _apply_overrides(data, overrides)

    try:
        return Theme.model_validate(data)
    except ValidationError as exc:
        # pydantic wraps validator exceptions, so re-raise as our own type.
        raise SpecError(f"invalid theme {ref!r}: {exc}") from exc
```

Import `ValidationError` from pydantic and `SpecError` from `.errors` alongside the existing imports. `SpecError` subclasses `PrismError`, so the weight test's `pytest.raises(PrismError)` catches it.

Note: `UnknownToken`'s message says "token", which reads correctly for both a bad theme name and a bad dotted path.

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_theme.py -v`
Expected: PASS (9 tests)

Pydantic wraps validator exceptions in `ValidationError`, so `test_weight_other_than_400_or_700_is_rejected` may fail. If it does, catch `ValidationError` in `load_theme` and re-raise as `SpecError` with the original message — that is behaviour we want anyway, so make it explicit rather than loosening the test.

- [x] **Step 5: Commit**

```bash
git add prism/theme.py prism/themes/ tests/test_theme.py
git commit -m "feat(theme): token-based themes with dotted overrides"
```

---

### Task 8: Vendor Lucide icons

**Files:**
- Create: `scripts/build_icons.py`, `prism/vendor/lucide/icons.json`, `prism/vendor/lucide/LICENSE`, `prism/icons.py`, `tests/test_icons.py`

**Interfaces:**
- Produces:
  - `icons.json`: `{"version": "1.27.0", "icons": {"<name>": "<path d string>"}}`.
  - `icon_names() -> list[str]`, `build_icon(name: str, size: float, color: Color, stroke: float) -> IconShape`.

Every Lucide icon is uniform 24×24, `fill="none"`, `stroke="currentColor"`, `stroke-width="2"`, round caps — so icons inherit theme tokens like any other geometry. The build script normalizes `rect`, `circle`, `line`, `polyline` and `polygon` children into a single `d` string.

**Important correction to the spec:** `tesserax.Path` has no raw `d` attribute — it builds an internal `_commands` list through `jump_to` / `line_to` / `cubic_to` / `arc` / `close` and derives its bounds from the points it has seen. So prism cannot hand it a `d` string. VS1 therefore renders icons through a small `IconShape(Visual)` that emits the `<path>` directly and reports exact bounds, which it can do because the source viewBox is known to be 24×24. The consequence: **`texture: sketch` will not apply to icons in v1**, because tesserax's sketch pass works through `trace()`. Revisit in VS2 — either write a `d`-parser that feeds a real `tesserax.Path`, or accept clean icons inside sketch diagrams as a deliberate look.

- [x] **Step 1: Write the failing test**

```python
# tests/test_icons.py
import pytest
from tesserax.color import hex as parse_hex

from prism.errors import UnknownIcon
from prism.icons import build_icon, icon_names

INK = parse_hex("#111827")


def test_known_icons_are_available():
    names = icon_names()
    assert "database" in names
    assert "users" in names
    assert len(names) > 500


def test_icon_bounds_are_exactly_the_requested_size():
    bounds = build_icon("database", size=16, color=INK, stroke=1.5).local()
    assert bounds.width == 16
    assert bounds.height == 16


def test_icon_scales_to_requested_size():
    small = build_icon("database", size=16, color=INK, stroke=1.5).local()
    large = build_icon("database", size=32, color=INK, stroke=1.5).local()
    assert large.width > small.width


def test_unknown_icon_raises_with_suggestion():
    with pytest.raises(UnknownIcon) as excinfo:
        build_icon("databse", size=16, color=INK, stroke=1.5)
    assert "database" in str(excinfo.value)


def test_icon_renders_as_an_unfilled_stroked_path():
    svg = build_icon("database", size=16, color=INK, stroke=1.5).render()
    assert "<path" in svg
    assert 'fill="none"' in svg


def test_stroke_width_compensates_for_scaling():
    """A 16px icon and a 32px icon must have visually equal stroke weight."""
    small = build_icon("database", size=16, color=INK, stroke=1.5).render()
    large = build_icon("database", size=32, color=INK, stroke=1.5).render()
    assert small != large
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_icons.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.icons'`

- [x] **Step 3: Write minimal implementation**

```python
# scripts/build_icons.py
"""Vendor Lucide icons as normalized path data.

    uv run python scripts/build_icons.py

Downloads a pinned Lucide release, converts every icon's child elements to a
single SVG path `d` string, and writes prism/vendor/lucide/icons.json.
"""

from __future__ import annotations

import io
import json
import math
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = "1.27.0"
URL = f"https://github.com/lucide-icons/lucide/archive/refs/tags/{VERSION}.tar.gz"
OUT_DIR = Path(__file__).parent.parent / "prism" / "vendor" / "lucide"


def _rounded_rect(x, y, w, h, rx, ry) -> str:
    if rx <= 0 and ry <= 0:
        return f"M{x} {y}h{w}v{h}h{-w}Z"
    rx = rx or ry
    ry = ry or rx
    return (
        f"M{x + rx} {y}"
        f"h{w - 2 * rx}a{rx} {ry} 0 0 1 {rx} {ry}"
        f"v{h - 2 * ry}a{rx} {ry} 0 0 1 {-rx} {ry}"
        f"h{-(w - 2 * rx)}a{rx} {ry} 0 0 1 {-rx} {-ry}"
        f"v{-(h - 2 * ry)}a{rx} {ry} 0 0 1 {rx} {-ry}Z"
    )


def _circle(cx, cy, r) -> str:
    return f"M{cx - r} {cy}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0Z"


def _ellipse(cx, cy, rx, ry) -> str:
    return f"M{cx - rx} {cy}a{rx} {ry} 0 1 0 {2 * rx} 0a{rx} {ry} 0 1 0 {-2 * rx} 0Z"


def _points_to_path(points: str, close: bool) -> str:
    coords = [float(v) for v in points.replace(",", " ").split()]
    pairs = list(zip(coords[0::2], coords[1::2]))
    if not pairs:
        return ""
    head = f"M{pairs[0][0]} {pairs[0][1]}"
    tail = "".join(f"L{x} {y}" for x, y in pairs[1:])
    return head + tail + ("Z" if close else "")


def _f(element: ET.Element, name: str, default: float = 0.0) -> float:
    value = element.get(name)
    return float(value) if value is not None else default


def convert(svg_text: str) -> str:
    root = ET.fromstring(svg_text)
    parts: list[str] = []
    for child in root:
        tag = child.tag.rsplit("}", 1)[-1]
        match tag:
            case "path":
                parts.append(child.get("d", ""))
            case "rect":
                parts.append(
                    _rounded_rect(
                        _f(child, "x"),
                        _f(child, "y"),
                        _f(child, "width"),
                        _f(child, "height"),
                        _f(child, "rx"),
                        _f(child, "ry"),
                    )
                )
            case "circle":
                parts.append(_circle(_f(child, "cx"), _f(child, "cy"), _f(child, "r")))
            case "ellipse":
                parts.append(
                    _ellipse(
                        _f(child, "cx"),
                        _f(child, "cy"),
                        _f(child, "rx"),
                        _f(child, "ry"),
                    )
                )
            case "line":
                parts.append(
                    f"M{_f(child, 'x1')} {_f(child, 'y1')}"
                    f"L{_f(child, 'x2')} {_f(child, 'y2')}"
                )
            case "polyline":
                parts.append(_points_to_path(child.get("points", ""), close=False))
            case "polygon":
                parts.append(_points_to_path(child.get("points", ""), close=True))
            case _:
                raise SystemExit(f"unhandled Lucide element <{tag}>")
    return "".join(p for p in parts if p)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"downloading Lucide {VERSION}…")
    with urllib.request.urlopen(URL) as response:
        blob = response.read()

    icons: dict[str, str] = {}
    licence = ""
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if len(parts) == 2 and parts[1] == "LICENSE":
                licence = archive.extractfile(member).read().decode()
            if len(parts) != 3 or parts[1] != "icons":
                continue
            if not member.name.endswith(".svg"):
                continue
            name = Path(member.name).stem
            svg_text = archive.extractfile(member).read().decode()
            icons[name] = convert(svg_text)

    (OUT_DIR / "icons.json").write_text(
        json.dumps({"version": VERSION, "icons": dict(sorted(icons.items()))}) + "\n"
    )
    (OUT_DIR / "LICENSE").write_text(licence)
    print(f"wrote {len(icons)} icons")


if __name__ == "__main__":
    main()
```

Run it:

```bash
uv run python scripts/build_icons.py
```

```python
# prism/icons.py
"""Lucide icons, vendored as normalized path data.

Lucide is ISC-licensed; the notice ships at prism/vendor/lucide/LICENSE.
Every icon is a 24x24 stroke outline, so it inherits theme ink and stroke width
like any other geometry.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import quoteattr

from tesserax.base import Visual
from tesserax.color import Color, Colors
from tesserax.core import Bounds

from .errors import UnknownIcon

_DATA = Path(__file__).parent / "vendor" / "lucide" / "icons.json"
VIEWBOX = 24.0


@lru_cache(maxsize=1)
def _icons() -> dict[str, str]:
    return json.loads(_DATA.read_text())["icons"]


def icon_names() -> list[str]:
    return list(_icons())


class IconShape(Visual):
    """A vendored Lucide icon, centred on the origin.

    The source viewBox is known to be 24x24, so bounds are exact without
    parsing the path data.
    """

    def __init__(self, name: str, size: float, color: Color, stroke: float) -> None:
        data = _icons()
        if name not in data:
            raise UnknownIcon(name, data)
        super().__init__(fill=Colors.Transparent, stroke=color, width=stroke)
        self.name = name
        self.size = size
        self._d = data[name]

    def local(self) -> Bounds:
        return Bounds(-self.size / 2, -self.size / 2, self.size, self.size)

    def _render(self) -> str:
        scale = self.size / VIEWBOX
        offset = -VIEWBOX / 2
        # Stroke is divided by the scale so it lands at the requested width
        # after the group transform is applied.
        return (
            f'<g transform="scale({scale}) translate({offset} {offset})">'
            f'<path d={quoteattr(self._d)} fill="none" '
            f'stroke="{self.stroke}" stroke-width="{self.width / scale}" '
            'stroke-linecap="round" stroke-linejoin="round"/></g>'
        )


def build_icon(name: str, size: float, color: Color, stroke: float) -> IconShape:
    """Return the named icon as a shape, scaled to `size` and centred on origin."""
    return IconShape(name, size, color, stroke)
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_icons.py -v`
Expected: PASS (5 tests)

- [x] **Step 5: Commit**

```bash
git add scripts/build_icons.py prism/vendor/lucide/ prism/icons.py tests/test_icons.py
git commit -m "feat(icons): vendor Lucide as normalized path data"
```

---

### Task 9: Shared node model and node box

**Files:**
- Create: `prism/nodes.py`, `prism/nodebox.py`, `tests/test_nodebox.py`

**Interfaces:**
- Produces:
  - `Node` pydantic model: `id`, `label`, `sublabel`, `icon`, `badge`, `accent`, `emphasis`, `note`.
  - `RenderContext` dataclass: `theme: Theme`, `width: float`, `rng: random.Random`.
  - `build_node_box(node: Node, ctx: RenderContext, max_width: float = 160) -> tesserax.Container`.

`build_node_box` is the single place that decides what a node *looks* like, shared by all ten archetypes. Getting it right once is most of the visual quality.

- [x] **Step 1: Write the failing test**

```python
# tests/test_nodebox.py
import random

import pytest
from pydantic import ValidationError

from prism.nodebox import RenderContext, build_node_box
from prism.nodes import Node
from prism.theme import load_theme
from prism.typography import measure


@pytest.fixture
def ctx():
    return RenderContext(theme=load_theme("default"), width=900, rng=random.Random(0))


def test_node_requires_a_label():
    with pytest.raises(ValidationError):
        Node()


def test_node_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        Node(label="Ingest", colour="red")


def test_node_badge_is_length_limited():
    with pytest.raises(ValidationError):
        Node(label="Ingest", badge="toolong")


def test_box_contains_its_label(ctx):
    node = Node(label="Ingest")
    box = build_node_box(node, ctx)
    inner = box.local().width - 2 * ctx.theme.geometry.pad
    assert measure("Ingest", ctx.theme.size("label"), weight=700) <= inner


def test_long_label_wraps_instead_of_overflowing(ctx):
    node = Node(label="Ingest raw events from the upstream bus")
    box = build_node_box(node, ctx, max_width=120)
    assert box.local().width <= 120 + 2 * ctx.theme.geometry.pad


def test_sublabel_makes_the_box_taller(ctx):
    plain = build_node_box(Node(label="Ingest"), ctx).local().height
    with_sub = (
        build_node_box(Node(label="Ingest", sublabel="S3 + Kafka"), ctx).local().height
    )
    assert with_sub > plain


def test_icon_makes_the_box_wider(ctx):
    plain = build_node_box(Node(label="Ingest"), ctx).local().width
    with_icon = build_node_box(Node(label="Ingest", icon="database"), ctx).local().width
    assert with_icon > plain


def test_accent_index_colours_the_border(ctx):
    box = build_node_box(Node(label="Ingest", accent=1), ctx)
    assert str(box.stroke) == str(ctx.theme.color(1))


def test_muted_emphasis_uses_the_muted_token(ctx):
    box = build_node_box(Node(label="Ingest", emphasis="muted"), ctx)
    assert str(box.stroke) == str(ctx.theme.color("muted"))
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_nodebox.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.nodebox'`

- [x] **Step 3: Write minimal implementation**

```python
# prism/nodes.py
"""The rich node every archetype shares."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    label: str
    sublabel: str | None = None
    icon: str | None = None
    badge: str | None = Field(default=None, max_length=4)
    accent: int | str | None = None
    emphasis: Literal["strong", "normal", "muted"] = "normal"
    note: str | None = None


class GroupSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    members: list[str] = Field(min_length=1)
    accent: int | str | None = None


class Link(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    source: str = Field(alias="from")
    target: str = Field(alias="to")
    label: str | None = None
    style: Literal["solid", "dashed", "dotted"] = "solid"
    kind: Literal["forward", "back", "bidirectional"] = "forward"
```

```python
# prism/nodebox.py
"""How a Node is drawn. Shared by every archetype."""

from __future__ import annotations

import random
from dataclasses import dataclass

from tesserax import Container, Group
from tesserax.layout import ColumnLayout, RowLayout

from .icons import build_icon
from .nodes import Node
from .text import TextBlock
from .theme import Theme


@dataclass
class RenderContext:
    theme: Theme
    width: float
    rng: random.Random


def _border_color(node: Node, theme: Theme):
    if node.emphasis == "muted":
        return theme.color("muted")
    if node.accent is not None:
        return theme.color(node.accent)
    return theme.color("line")


def build_node_box(node: Node, ctx: RenderContext, max_width: float = 160) -> Container:
    theme = ctx.theme
    ink = theme.color("ink") if node.emphasis != "muted" else theme.color("muted")

    stack: list = [
        TextBlock(
            node.label,
            max_width,
            size=theme.size("label"),
            fill=ink,
            family=theme.typography.family,
            weight=theme.weight("label"),
            line_height=theme.typography.line_height,
        )
    ]

    if node.sublabel:
        stack.append(
            TextBlock(
                node.sublabel,
                max_width,
                size=theme.size("sublabel"),
                fill=theme.color("muted"),
                family=theme.typography.family,
                weight=theme.weight("sublabel"),
                line_height=theme.typography.line_height,
            )
        )

    body: Group = ColumnLayout(stack, align="middle", gap=theme.geometry.gap / 6)

    if node.icon:
        glyph = build_icon(
            node.icon,
            size=theme.size("label") * 1.4,
            color=ink,
            stroke=theme.geometry.stroke,
        )
        body = RowLayout([glyph, body], align="middle", gap=theme.geometry.pad / 2)

    return Container(
        [body],
        padding=theme.geometry.pad,
        corner_radius=theme.geometry.radius,
        fill=theme.color("surface"),
        stroke=_border_color(node, theme),
        width=theme.geometry.stroke * (2 if node.emphasis == "strong" else 1),
    )
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_nodebox.py -v`
Expected: PASS (9 tests)

- [x] **Step 5: Commit**

```bash
git add prism/nodes.py prism/nodebox.py tests/test_nodebox.py
git commit -m "feat(nodes): shared Node model and node box builder"
```

---

### Task 10: Envelope and registry

**Files:**
- Create: `prism/envelope.py`, `prism/registry.py`, `tests/test_envelope.py`, `tests/test_registry.py`

**Interfaces:**
- Produces:
  - `Envelope` model: `type`, `theme` (default `"default"`), `title`, `subtitle`, `caption`, `width` (default `900`), `tokens` (dict of dotted path → value).
  - `load_spec(source: str | Path) -> dict` — accepts a file path or raw YAML text; raises `SpecError` when there is no top-level `type`.
  - `Archetype` protocol: `name: str`, `spec_model: type[BaseModel]`, `build(spec, ctx) -> tesserax.Group`.
  - `ARCHETYPES: dict[str, Archetype]`, `register(archetype)`, `get(name) -> Archetype` (raises `UnknownArchetype`).

- [x] **Step 1: Write the failing test**

```python
# tests/test_envelope.py
import pytest

from prism.envelope import Envelope, load_spec
from prism.errors import SpecError


def test_load_spec_reads_yaml_text():
    data = load_spec("type: flow\nsteps: [{label: A}]\n")
    assert data["type"] == "flow"


def test_load_spec_reads_a_file(tmp_path):
    path = tmp_path / "d.yaml"
    path.write_text("type: flow\nsteps: [{label: A}]\n")
    assert load_spec(path)["type"] == "flow"


def test_spec_without_type_is_rejected():
    with pytest.raises(SpecError):
        load_spec("steps: [{label: A}]\n")


def test_non_mapping_spec_is_rejected():
    with pytest.raises(SpecError):
        load_spec("- just\n- a list\n")


def test_envelope_defaults():
    env = Envelope(type="flow")
    assert env.theme == "default"
    assert env.width == 900
    assert env.tokens == {}


def test_envelope_ignores_archetype_payload_keys():
    env = Envelope.model_validate({"type": "flow", "steps": [{"label": "A"}]})
    assert env.type == "flow"
```

```python
# tests/test_registry.py
import pytest
from pydantic import BaseModel

from prism.errors import UnknownArchetype
from prism.registry import get, register


class _Dummy(BaseModel):
    pass


class _Fake:
    name = "fake"
    spec_model = _Dummy

    def build(self, spec, ctx):
        raise NotImplementedError


def test_registered_archetype_is_retrievable():
    register(_Fake())
    assert get("fake").name == "fake"


def test_unknown_archetype_raises_with_suggestion():
    register(_Fake())
    with pytest.raises(UnknownArchetype) as excinfo:
        get("fkae")
    assert "fake" in str(excinfo.value)
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_envelope.py tests/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.envelope'`

- [x] **Step 3: Write minimal implementation**

```python
# prism/envelope.py
"""The common shell every prism spec shares."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from .errors import SpecError


class Envelope(BaseModel):
    # Archetype payload keys live alongside these, so extras are ignored here.
    model_config = ConfigDict(extra="ignore")

    type: str
    theme: str = "default"
    title: str | None = None
    subtitle: str | None = None
    caption: str | None = None
    width: float = 900
    tokens: dict[str, Any] = {}


def load_spec(source: str | Path) -> dict:
    """Load a spec from a file path or from raw YAML text."""
    text = str(source)
    if len(text) < 4096 and os.path.exists(text):
        text = Path(text).read_text()

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SpecError(f"spec is not valid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise SpecError(
            "a prism spec must be a YAML mapping with a top-level 'type' field"
        )
    if "type" not in data:
        raise SpecError(
            "a prism spec needs a top-level 'type' field naming the archetype"
        )
    return data
```

```python
# prism/registry.py
"""Archetype registry — maps a spec `type` to its builder."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel
from tesserax import Group

from .errors import UnknownArchetype
from .nodebox import RenderContext


@runtime_checkable
class Archetype(Protocol):
    """A deterministic, network-free diagram builder for one spec `type`."""

    name: str
    spec_model: type[BaseModel]

    def build(self, spec: BaseModel, ctx: RenderContext) -> Group: ...


ARCHETYPES: dict[str, Archetype] = {}


def register(archetype: Archetype) -> None:
    ARCHETYPES[archetype.name] = archetype


def get(name: str) -> Archetype:
    if name not in ARCHETYPES:
        raise UnknownArchetype(name, ARCHETYPES)
    return ARCHETYPES[name]


def names() -> list[str]:
    return sorted(ARCHETYPES)
```

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_envelope.py tests/test_registry.py -v`
Expected: PASS (8 tests)

- [x] **Step 5: Commit**

```bash
git add prism/envelope.py prism/registry.py tests/test_envelope.py tests/test_registry.py
git commit -m "feat(core): spec envelope and archetype registry"
```

---

### Task 11: The `flow` archetype

**Files:**
- Create: `prism/archetypes/__init__.py`, `prism/archetypes/flow/__init__.py`, `prism/archetypes/flow/schema.py`, `prism/archetypes/flow/build.py`, `tests/test_flow.py`

**Interfaces:**
- Consumes: `Node`, `RenderContext`, `build_node_box`, `register`.
- Produces: `FlowSpec` (fields `direction: "right" | "down"`, `steps: list[Node]` with `min_length=1`) and a registered `FlowArchetype` with `name = "flow"`.

VS1 implements the linear spine only. `branches`, `lanes`, `phases`, `links` and `groups` are additive fields that arrive in VS3 — adding them later breaks no existing spec.

- [x] **Step 1: Write the failing test**

```python
# tests/test_flow.py
import random

import pytest
from pydantic import ValidationError

from prism.archetypes.flow.schema import FlowSpec
from prism.nodebox import RenderContext
from prism.registry import get
from prism.theme import load_theme


@pytest.fixture
def ctx():
    return RenderContext(theme=load_theme("default"), width=900, rng=random.Random(0))


def test_flow_is_registered():
    assert get("flow").name == "flow"


def test_flow_requires_at_least_one_step():
    with pytest.raises(ValidationError):
        FlowSpec(steps=[])


def test_flow_defaults_to_left_to_right():
    assert FlowSpec(steps=[{"label": "A"}]).direction == "right"


def test_horizontal_flow_is_wider_than_tall(ctx):
    spec = FlowSpec(steps=[{"label": "A"}, {"label": "B"}, {"label": "C"}])
    bounds = get("flow").build(spec, ctx).local()
    assert bounds.width > bounds.height


def test_vertical_flow_is_taller_than_wide(ctx):
    spec = FlowSpec(
        direction="down", steps=[{"label": "A"}, {"label": "B"}, {"label": "C"}]
    )
    bounds = get("flow").build(spec, ctx).local()
    assert bounds.height > bounds.width


def test_flow_draws_one_connector_between_each_pair(ctx):
    spec = FlowSpec(steps=[{"label": "A"}, {"label": "B"}, {"label": "C"}])
    svg = get("flow").build(spec, ctx).render()
    assert svg.count("marker-end") == 2


def test_single_step_flow_has_no_connectors(ctx):
    spec = FlowSpec(steps=[{"label": "A"}])
    assert "marker-end" not in get("flow").build(spec, ctx).render()


def test_steps_grow_the_diagram(ctx):
    two = (
        get("flow")
        .build(FlowSpec(steps=[{"label": "A"}, {"label": "B"}]), ctx)
        .local()
        .width
    )
    four = (
        get("flow")
        .build(
            FlowSpec(
                steps=[{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}]
            ),
            ctx,
        )
        .local()
        .width
    )
    assert four > two
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_flow.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.archetypes'`

- [x] **Step 3: Write minimal implementation**

```python
# prism/archetypes/flow/schema.py
"""Schema for the `flow` archetype."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class FlowSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["right", "down"] = "right"
    steps: list[Node] = Field(min_length=1)
```

```python
# prism/archetypes/flow/build.py
"""Compose a linear flow of steps connected by arrows."""

from __future__ import annotations

from tesserax import Arrow, Group
from tesserax.layout import ColumnLayout, RowLayout

from ...nodebox import RenderContext, build_node_box
from .schema import FlowSpec


class FlowArchetype:
    name = "flow"
    spec_model = FlowSpec

    def build(self, spec: FlowSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        boxes = [build_node_box(step, ctx) for step in spec.steps]

        if spec.direction == "right":
            spine = RowLayout(boxes, align="middle", gap=theme.geometry.gap)
            tail, head = "right", "left"
        else:
            spine = ColumnLayout(boxes, align="middle", gap=theme.geometry.gap)
            tail, head = "bottom", "top"

        connectors = [
            Arrow(
                boxes[i].anchor(tail),
                boxes[i + 1].anchor(head),
                stroke=theme.color("line"),
                width=theme.geometry.stroke,
            )
            for i in range(len(boxes) - 1)
        ]

        return Group([spine, *connectors])
```

```python
# prism/archetypes/flow/__init__.py
from ...registry import register
from .build import FlowArchetype
from .schema import FlowSpec

register(FlowArchetype())

__all__ = ["FlowArchetype", "FlowSpec"]
```

```python
# prism/archetypes/__init__.py
"""Importing this package registers every bundled archetype."""

from . import flow  # noqa: F401

__all__ = ["flow"]
```

Two things to verify against tesserax while implementing, rather than assuming:
1. `Group.anchor(name)` returns a `Point` in the *parent's* coordinate space after the layout has run. If arrows land in the wrong place, the layout has not been applied at the time `anchor()` is evaluated — pass the callables form (`Arrow` accepts `Callable[[], Point]`) so resolution is deferred.
2. Adding `spine` and `connectors` to one `Group` must not re-parent the boxes. `Group.add` raises `RuntimeError` on a shape that already has a parent unless `mode="loose"`. The boxes belong to `spine`; the connectors reference them but must not contain them.

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_flow.py -v`
Expected: PASS (8 tests)

- [x] **Step 5: Commit**

```bash
git add prism/archetypes/ tests/test_flow.py
git commit -m "feat(flow): linear flow archetype"
```

---

### Task 12: Framing and the public render API

**Files:**
- Create: `prism/frame.py`, `tests/test_render.py`
- Modify: `prism/__init__.py`

**Interfaces:**
- Produces:
  - `frame(body: Group, envelope: Envelope, ctx: RenderContext) -> Canvas` — stacks title, subtitle, body and caption; fits; adds `role="img"`, `<title>` and `<desc>`.
  - `prism.render_str(source: str | Path) -> str`.
  - `prism.render(source: str | Path, out_path: str | Path) -> Path`.

Two behaviours belong here and nowhere else: the deterministic RNG seed, and the guard against tesserax's global `Group.stack`.

- [x] **Step 1: Write the failing test**

```python
# tests/test_render.py
import tesserax
import pytest

import prism
from prism.errors import SpecError, UnknownArchetype

SPEC = """
type: flow
title: Ingestion
caption: Source: internal
steps:
  - label: Ingest
    icon: database
  - label: Verify
  - label: Publish
"""


def test_render_str_emits_svg():
    svg = prism.render_str(SPEC)
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")


def test_render_writes_a_file(tmp_path):
    out = prism.render(SPEC, tmp_path / "d.svg")
    assert out.exists()
    assert out.read_text().startswith("<svg")


def test_title_and_caption_appear_in_the_output():
    svg = prism.render_str(SPEC)
    assert "Ingestion" in svg
    assert "internal" in svg


def test_output_carries_accessibility_metadata():
    svg = prism.render_str(SPEC)
    assert 'role="img"' in svg
    assert "<title>" in svg
    assert "<desc>" in svg


def test_rendering_is_deterministic():
    assert prism.render_str(SPEC) == prism.render_str(SPEC)


def test_unknown_archetype_raises():
    with pytest.raises(UnknownArchetype):
        prism.render_str("type: flowchart\nsteps: [{label: A}]\n")


def test_invalid_payload_raises_spec_error():
    with pytest.raises(SpecError):
        prism.render_str("type: flow\nsteps: []\n")


def test_unknown_field_raises_spec_error():
    with pytest.raises(SpecError):
        prism.render_str("type: flow\nsteps: [{label: A, colour: red}]\n")


def test_inline_token_overrides_apply():
    svg = prism.render_str(SPEC + "tokens:\n  palette.ink: '#ff0000'\n")
    assert "#ff0000" in svg.lower()


def test_render_does_not_leak_into_a_users_canvas():
    """tesserax's Group.stack is global; prism must not attach shapes to it."""
    with tesserax.Canvas() as canvas:
        prism.render_str(SPEC)
    assert canvas.shapes == []
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_render.py -v`
Expected: FAIL — `AttributeError: module 'prism' has no attribute 'render_str'`

- [x] **Step 3: Write minimal implementation**

```python
# prism/frame.py
"""Wrap an archetype's body with title, caption and accessibility metadata."""

from __future__ import annotations

from xml.sax.saxutils import escape

from tesserax import Canvas, Group
from tesserax.layout import ColumnLayout

from .envelope import Envelope
from .nodebox import RenderContext
from .text import TextBlock


def frame(body: Group, envelope: Envelope, ctx: RenderContext) -> Canvas:
    theme = ctx.theme
    parts: list = []

    if envelope.title:
        parts.append(
            TextBlock(
                envelope.title,
                envelope.width,
                size=theme.size("title"),
                fill=theme.color("ink"),
                family=theme.typography.family,
                weight=theme.weight("title"),
                line_height=theme.typography.line_height,
            )
        )
    if envelope.subtitle:
        parts.append(
            TextBlock(
                envelope.subtitle,
                envelope.width,
                size=theme.size("subtitle"),
                fill=theme.color("muted"),
                family=theme.typography.family,
                weight=theme.weight("sublabel"),
                line_height=theme.typography.line_height,
            )
        )

    parts.append(body)

    if envelope.caption:
        parts.append(
            TextBlock(
                envelope.caption,
                envelope.width,
                size=theme.size("note"),
                fill=theme.color("muted"),
                family=theme.typography.family,
                weight=theme.weight("note"),
                line_height=theme.typography.line_height,
            )
        )

    stacked = ColumnLayout(parts, align="middle", gap=theme.geometry.gap)

    canvas = Canvas(width=envelope.width, height=envelope.width)
    canvas.add(stacked, mode="loose")
    canvas.fit(padding=theme.geometry.gap)
    return canvas


def with_accessibility(svg: str, envelope: Envelope) -> str:
    """Inject role, <title> and <desc> into a rendered SVG."""
    title = escape(envelope.title or f"{envelope.type} diagram")
    desc = escape(envelope.caption or envelope.subtitle or title)
    head, rest = svg.split(">", 1)
    return f'{head} role="img">\n<title>{title}</title>\n<desc>{desc}</desc>{rest}'
```

```python
# prism/__init__.py
"""Declarative YAML to SVG diagrams."""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

import yaml
from pydantic import ValidationError
from tesserax.base import Group as _TGroup

from . import archetypes as _archetypes  # noqa: F401  (registers the catalog)
from .envelope import Envelope, load_spec
from .errors import PrismError, SpecError
from .frame import frame, with_accessibility
from .nodebox import RenderContext
from .registry import get
from .theme import load_theme

__version__ = "0.1.0.dev0"

__all__ = ["render", "render_str", "PrismError", "SpecError", "__version__"]

_ENVELOPE_KEYS = set(Envelope.model_fields)


def _seed(data: dict) -> int:
    canonical = yaml.safe_dump(data, sort_keys=True).encode()
    return int.from_bytes(hashlib.blake2b(canonical, digest_size=8).digest(), "big")


def render_str(source: str | Path) -> str:
    """Render a spec to an SVG string."""
    data = load_spec(source)
    envelope = Envelope.model_validate(data)
    archetype = get(envelope.type)

    payload = {k: v for k, v in data.items() if k not in _ENVELOPE_KEYS}
    try:
        spec = archetype.spec_model.model_validate(payload)
    except ValidationError as exc:
        raise SpecError(f"invalid '{envelope.type}' spec: {exc}") from exc

    theme = load_theme(envelope.theme, envelope.tokens or None)
    ctx = RenderContext(
        theme=theme, width=envelope.width, rng=random.Random(_seed(data))
    )

    # tesserax auto-attaches every constructed Shape to the innermost active
    # `with Group(...)`. That stack is a class-level global, so a caller who
    # renders inside their own canvas would otherwise collect our shapes.
    saved, _TGroup.stack = _TGroup.stack, []
    try:
        canvas = frame(archetype.build(spec, ctx), envelope, ctx)
    finally:
        _TGroup.stack = saved

    return with_accessibility(canvas._repr_svg_(), envelope)


def render(source: str | Path, out_path: str | Path) -> Path:
    """Render a spec and write it to `out_path`. Returns the path written."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_str(source), encoding="utf-8")
    return out
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_render.py -v`
Expected: PASS (10 tests)

- [x] **Step 5: Commit**

```bash
git add prism/frame.py prism/__init__.py tests/test_render.py
git commit -m "feat(render): framing, accessibility, determinism and public API"
```

---

### Task 13: CLI, golden test, and README

**Files:**
- Create: `prism/cli.py`, `examples/flow-ingestion.yaml`, `tests/golden/flow-ingestion.svg`, `tests/test_golden.py`, `tests/test_cli.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `main(argv: list[str] | None = None) -> int` backing the `prism` console script, with subcommands `render`, `themes`, `icons`, `archetypes`.

The golden test is the regression guard for the whole stack. Coordinates are rounded before comparison so float noise across platforms cannot cause false failures.

- [x] **Step 1: Write the failing test**

```yaml
# examples/flow-ingestion.yaml
type: flow
title: Ingestion pipeline
subtitle: as of Q3
caption: "Source: internal architecture review"
direction: right
steps:
  - id: ingest
    label: Ingest
    sublabel: S3 + Kafka
    icon: database
    accent: 0
  - id: verify
    label: Verify
    sublabel: schema + dedupe
    icon: shield-check
    accent: 1
  - id: publish
    label: Publish
    sublabel: warehouse
    icon: send
    accent: 2
    emphasis: strong
```

```python
# tests/test_golden.py
import re
from pathlib import Path

import prism

EXAMPLE = Path(__file__).parent.parent / "examples" / "flow-ingestion.yaml"
GOLDEN = Path(__file__).parent / "golden" / "flow-ingestion.svg"

_NUMBER = re.compile(r"-?\d+\.\d+")


def normalize(svg: str) -> str:
    """Round every float to 2 decimals so platform noise cannot fail the test."""
    return _NUMBER.sub(lambda m: f"{float(m.group()):.2f}", svg)


def test_example_matches_golden():
    actual = normalize(prism.render_str(EXAMPLE))
    expected = normalize(GOLDEN.read_text())
    assert actual == expected, (
        "Rendered output changed. If this is intentional, regenerate with:\n"
        '  uv run python -c "import prism,pathlib; '
        "pathlib.Path('tests/golden/flow-ingestion.svg').write_text("
        "prism.render_str('examples/flow-ingestion.yaml'))\""
    )


def _text_blocks(shape):
    """Walk a shape tree yielding every TextBlock, wherever it was nested."""
    from prism.text import TextBlock

    if isinstance(shape, TextBlock):
        yield shape
        return
    for child in getattr(shape, "shapes", []):
        yield from _text_blocks(child)


def test_every_label_fits_its_box():
    """The regression guard for prism-owned typography."""
    import random

    from prism.nodebox import RenderContext, build_node_box
    from prism.nodes import Node
    from prism.theme import load_theme
    from prism.typography import measure

    theme = load_theme("default")
    ctx = RenderContext(theme=theme, width=900, rng=random.Random(0))
    labels = [
        "Ingest",
        "WWWWW MMMMM",
        "lllll iiiii",
        "Publish to the warehouse",
        "Supercalifragilisticexpialidocious",
    ]
    for label in labels:
        box = build_node_box(Node(label=label), ctx, max_width=160)
        inner = box.local().width - 2 * theme.geometry.pad
        blocks = list(_text_blocks(box))
        assert blocks, "node box contains no TextBlock"
        longest = max(
            measure(line, theme.size("label"), weight=theme.weight("label"))
            for block in blocks
            for line in block.lines
        )
        assert longest <= inner + 0.01, f"{label!r} overflows its box"
```

```python
# tests/test_cli.py
from prism.cli import main


def test_render_writes_output(tmp_path, capsys):
    out = tmp_path / "d.svg"
    assert main(["render", "examples/flow-ingestion.yaml", "-o", str(out)]) == 0
    assert out.read_text().startswith("<svg")


def test_render_to_stdout_when_no_output_given(capsys):
    assert main(["render", "examples/flow-ingestion.yaml"]) == 0
    assert capsys.readouterr().out.startswith("<svg")


def test_archetypes_lists_flow(capsys):
    assert main(["archetypes"]) == 0
    assert "flow" in capsys.readouterr().out


def test_themes_lists_default(capsys):
    assert main(["themes"]) == 0
    assert "default" in capsys.readouterr().out


def test_icons_lists_known_names(capsys):
    assert main(["icons"]) == 0
    assert "database" in capsys.readouterr().out


def test_bad_spec_exits_nonzero_with_a_readable_message(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("type: flowchart\nsteps: [{label: A}]\n")
    assert main(["render", str(bad)]) == 1
    assert "flow" in capsys.readouterr().err
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py tests/test_golden.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'prism.cli'`

- [x] **Step 3: Write minimal implementation**

```python
# prism/cli.py
"""Command-line interface."""

from __future__ import annotations

import argparse
import sys

from . import render, render_str
from .errors import PrismError
from .icons import icon_names
from .registry import names as archetype_names
from .theme import bundled_themes


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prism", description="Declarative YAML to SVG diagrams."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render_cmd = sub.add_parser("render", help="render a spec to SVG")
    render_cmd.add_argument("spec", help="path to a YAML spec")
    render_cmd.add_argument(
        "-o", "--output", help="output path; writes to stdout when omitted"
    )

    sub.add_parser("themes", help="list bundled themes")
    sub.add_parser("icons", help="list available icon names")
    sub.add_parser("archetypes", help="list available archetypes")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        match args.command:
            case "render":
                if args.output:
                    render(args.spec, args.output)
                else:
                    sys.stdout.write(render_str(args.spec))
            case "themes":
                print("\n".join(bundled_themes()))
            case "icons":
                print("\n".join(icon_names()))
            case "archetypes":
                print("\n".join(archetype_names()))
    except PrismError as exc:
        print(f"prism: {exc}", file=sys.stderr)
        return 1

    return 0
```

Generate the golden file once, **after eyeballing the output in a browser** — a golden that locks in an ugly diagram is worse than no golden:

```bash
uv run python -c "import prism, pathlib; pathlib.Path('tests/golden/flow-ingestion.svg').write_text(prism.render_str('examples/flow-ingestion.yaml'))"
xdg-open tests/golden/flow-ingestion.svg
```

Then rewrite `README.md`: what prism is, the `flow-ingestion.yaml` example, the rendered SVG inline, install instructions (`pip install prism-svg`), a note that the catalog is growing, and the tesserax + Lucide credits.

- [x] **Step 4: Run the full suite**

Run: `uv run pytest -v`
Expected: PASS (all tests across all files)

Then run the lint gate **as its own step and check its exit code** — never pipe it through `tail`, which masks the return code:

```bash
uv run ruff check .
uv run ruff format --check .
```

- [x] **Step 5: Commit**

```bash
git add prism/cli.py examples/ tests/golden/ tests/test_golden.py tests/test_cli.py README.md
git commit -m "feat(cli): render command, golden test and README"
```

---

## Definition of done for VS1

- `uv run pytest` is green; `uv run ruff check .` exits 0.
- `uv run prism render examples/flow-ingestion.yaml -o /tmp/flow.svg` produces an SVG that looks good in a browser — icons aligned, no label touching or crossing its border, arrows meeting box edges cleanly.
- `prism.render_str` called inside a user's `with tesserax.Canvas()` block leaves that canvas empty.
- Rendering the same spec twice is byte-identical.

## What VS1 deliberately leaves out

`branches`, `lanes`, `phases`, `links` and `groups` on `flow`; the other nine archetypes; the `dark`, `paper` and `mono` themes; `texture: sketch`; the curated icon vocabulary; `SKILL.md`; JSON Schema export; the Quarto extension; PNG export; the docs site. Each is a later vertical slice, and each is additive — no VS1 spec will break when they land.
