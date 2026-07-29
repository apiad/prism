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
            align=anchor,
            gap=size * (line_height - 1),
        )
