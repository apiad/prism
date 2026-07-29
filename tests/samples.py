"""The bundled examples, which are the single source of truth for the docs.

Tests read the same files the gallery renders and the README embeds, so a
broken example fails the build rather than shipping a broken picture.
"""

from __future__ import annotations

from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

SAMPLES: dict[str, str] = {
    path.stem: path.read_text() for path in sorted(EXAMPLES_DIR.glob("*.yaml"))
}
