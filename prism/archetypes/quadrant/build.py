"""A 2x2 field with named axes and positioned items."""

from __future__ import annotations

from tesserax import Circle, Group, Line, Rect
from tesserax.core import Point, Shape

from ...nodebox import RenderContext
from ...shapes import at, text_stack
from ...text import MeasuredText
from .schema import QuadrantSpec

SIZE = 400.0
DOT_RADIUS = 5.0


class QuadrantArchetype:
    name = "quadrant"
    spec_model = QuadrantSpec
    supports_note = False

    def build(self, spec: QuadrantSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        half = SIZE / 2

        field = Rect(
            SIZE,
            SIZE,
            fill=theme.color("surface"),
            stroke=theme.color("line"),
            width=theme.geometry.stroke,
        )
        crosshair = [
            Line(
                Point(-half, 0),
                Point(half, 0),
                stroke=theme.color("line"),
                width=theme.geometry.stroke,
            ),
            Line(
                Point(0, -half),
                Point(0, half),
                stroke=theme.color("line"),
                width=theme.geometry.stroke,
            ),
        ]

        shapes: list[Shape] = [field, *crosshair]
        shapes.extend(self._quadrant_captions(spec, ctx, half))
        shapes.extend(self._axis_captions(spec, ctx, half))

        for index, item in enumerate(spec.items):
            # y runs upward in the data, downward in SVG.
            px = (item.x - 0.5) * SIZE
            py = (0.5 - item.y) * SIZE
            accent = item.accent if item.accent is not None else index
            dot = Circle(
                DOT_RADIUS,
                fill=theme.color(accent),
                stroke=theme.color("surface"),
                width=theme.geometry.stroke,
            )
            at(dot, px, py)
            caption = text_stack(item, ctx, 130)
            at(
                caption,
                px,
                py - DOT_RADIUS - theme.geometry.pad / 2 - caption.local().height / 2,
            )
            shapes.extend([dot, caption])

        return Group(shapes)

    def _quadrant_captions(
        self, spec: QuadrantSpec, ctx: RenderContext, half: float
    ) -> list[Shape]:
        if not spec.quadrant_labels:
            return []
        theme = ctx.theme
        inset = theme.geometry.pad * 1.5
        # Reading order: top-left, top-right, bottom-left, bottom-right.
        corners = [
            (-half + inset, -half + inset, "start"),
            (half - inset, -half + inset, "end"),
            (-half + inset, half - inset, "start"),
            (half - inset, half - inset, "end"),
        ]
        captions: list[Shape] = []
        for text, (x, y, anchor) in zip(spec.quadrant_labels, corners, strict=False):
            tag = MeasuredText(
                text,
                size=theme.size("note"),
                fill=theme.color("muted"),
                family=theme.typography.family,
                weight=theme.weight("badge"),
                anchor=anchor,
            )
            offset = tag.local().width / 2
            at(tag, x + (offset if anchor == "start" else -offset), y)
            captions.append(tag)
        return captions

    def _axis_captions(
        self, spec: QuadrantSpec, ctx: RenderContext, half: float
    ) -> list[Shape]:
        theme = ctx.theme
        gap = theme.geometry.gap
        out: list[Shape] = []

        def caption(text: str, x: float, y: float, role: str = "sublabel") -> Shape:
            tag = MeasuredText(
                text,
                size=theme.size(role),
                fill=theme.color("muted" if role == "note" else "ink"),
                family=theme.typography.family,
                weight=theme.weight(role),
            )
            at(tag, x, y)
            return tag

        out.append(caption(spec.axes.x.label, 0, half + gap))
        # The y label is left-aligned above the field. Centring it there makes
        # it read as a second title under the diagram's own.
        y_label = caption(spec.axes.y.label, 0, -half - gap)
        at(y_label, -half + y_label.local().width / 2, -half - gap)
        out.append(y_label)
        if spec.axes.x.low:
            out.append(caption(spec.axes.x.low, -half, half + gap / 2, "note"))
        if spec.axes.x.high:
            out.append(caption(spec.axes.x.high, half, half + gap / 2, "note"))
        if spec.axes.y.low:
            out.append(caption(spec.axes.y.low, -half - gap, half, "note"))
        if spec.axes.y.high:
            out.append(caption(spec.axes.y.high, -half - gap, -half, "note"))
        return out
