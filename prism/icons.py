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
