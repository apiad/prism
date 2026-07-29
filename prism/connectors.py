"""Connectors between nodes, and the themed arrowhead they point with.

Two tesserax details shape this module:

* `Shape.anchor()` resolves through the whole parent chain and so returns
  *world* coordinates. A connector that is a sibling of the layout holding the
  boxes lives one transform below that, so feeding it world coordinates makes
  its parent's transform apply twice. `Shape.bounds()` is the right accessor:
  it is expressed in the parent's coordinate space.
* tesserax's built-in `arrow` marker is black and sized 10x8. SVG's default
  `markerUnits` is `strokeWidth`, so it renders at ten times the stroke width.
  prism defines its own, in theme colours and at a sane size.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from tesserax import Arrow, Canvas, Path
from tesserax.core import Point

from .theme import Theme

MARKER_ID = "prism-arrow"

Side = Literal["left", "right", "top", "bottom"]


def define_arrowhead(canvas: Canvas, theme: Theme) -> None:
    """Register prism's arrowhead on `canvas` so connectors can reference it."""
    head = (
        Path(fill=theme.color("muted"), stroke=theme.color("muted"), width=0)
        .jump_to(-5, -2)
        .line_to(0, 0)
        .line_to(-5, 2)
        .close()
    )
    canvas.define(MARKER_ID, head)


def _side(shape, side: Side) -> Callable[[], Point]:
    """A deferred accessor for one side of `shape`, in its parent's space."""
    return lambda: getattr(shape.bounds(), side)


def connect(
    shape_from, shape_to, side_from: Side, side_to: Side, theme: Theme
) -> Arrow:
    """An arrow from one shape's side to another's, resolved at render time."""
    return Arrow(
        _side(shape_from, side_from),
        _side(shape_to, side_to),
        stroke=theme.color("muted"),
        width=theme.geometry.stroke,
        marker_end=MARKER_ID,
    )
