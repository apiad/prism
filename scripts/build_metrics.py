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
