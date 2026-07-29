"""Vendor Lucide icons as normalized path data.

    uv run python scripts/build_icons.py

Downloads a pinned Lucide release, converts every icon's child elements to a
single SVG path `d` string, and writes prism/vendor/lucide/icons.json.
"""

from __future__ import annotations

import io
import json
import re
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


_NUMBER = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
_LEADING_REL_MOVE = re.compile(rf"^m\s*({_NUMBER})[,\s]*({_NUMBER})\s*(.*)$", re.DOTALL)


def _absolutize_start(d: str) -> str:
    """Force a subpath to begin with an absolute moveto.

    Lucide writes a composite icon's later subpaths as their own <path>
    elements starting with a lowercase `m`. Alone that is relative to (0,0) and
    so behaves absolutely, but concatenated after another subpath it is
    relative to the previous endpoint, which displaces the whole subpath.

    Uppercasing the `m` alone is NOT enough: a moveto's trailing coordinate
    pairs are implicit linetos inheriting the moveto's case, so `m9 12 2 2 4-4`
    means three *relative* operations. Promoting only the command letter would
    silently reinterpret those pairs as absolute. We therefore emit an explicit
    relative `l` for the remainder.
    """
    stripped = d.strip()
    if not stripped.startswith("m"):
        return stripped

    match = _LEADING_REL_MOVE.match(stripped)
    if match is None:
        raise SystemExit(f"cannot normalize relative moveto in {d!r}")

    x, y, rest = match.groups()
    rest = rest.lstrip(", \t\r\n")
    if rest and (rest[0].isdigit() or rest[0] in "+-."):
        return f"M{x} {y}l{rest}"
    return f"M{x} {y}{rest}"


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
    return "".join(_absolutize_start(p) for p in parts if p.strip())


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
