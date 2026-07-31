"""Layered magnitude. Inverted, the same geometry reads as a funnel."""

from __future__ import annotations

from tesserax import Group
from tesserax.core import Shape

from ...nodebox import RenderContext
from ...shapes import at, natural_width, text_stack, trapezoid
from .schema import PyramidSpec

WIDTH = 420.0
NARROW = 0.28
OUTSIDE_WIDTH = 200.0
MIN_BAND_FRACTION = 0.06


class PyramidArchetype:
    name = "pyramid"
    spec_model = PyramidSpec
    supports_note = False

    def build(self, spec: PyramidSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        levels = spec.levels
        widths = self._boundary_widths(spec)

        probes = [text_stack(level, ctx, WIDTH * 0.6) for level in levels]
        height = max(
            max(p.local().height for p in probes) + theme.geometry.pad,
            theme.size("label") * 2.4,
        )
        pitch = height + theme.geometry.stroke * 2

        shapes: list[Shape] = []
        for index, level in enumerate(levels):
            top_width, bottom_width = widths[index], widths[index + 1]
            accent = level.accent if level.accent is not None else index
            y = (index - (len(levels) - 1) / 2) * pitch

            band = trapezoid(
                top_width,
                bottom_width,
                height,
                fill=theme.color("surface"),
                stroke=theme.color(accent),
                stroke_width=theme.geometry.stroke,
            )
            at(band, 0, y)
            shapes.append(band)

            # A band narrower than its own label gets the label alongside it,
            # which is what hand-drawn pyramids and funnels do. Forcing it
            # inside would wrap the text to one character per line.
            inner = min(top_width, bottom_width) - 2 * theme.geometry.pad
            if natural_width(level, ctx) <= inner:
                inside = text_stack(level, ctx, inner)
                at(inside, 0, y)
                shapes.append(inside)
                continue

            outside = text_stack(level, ctx, OUTSIDE_WIDTH)
            offset = max(top_width, bottom_width) / 2 + theme.geometry.gap
            at(outside, offset + outside.local().width / 2, y)
            shapes.append(outside)

        return Group(shapes)

    def _boundary_widths(self, spec: PyramidSpec) -> list[float]:
        """One width per band boundary, in reading order (top first)."""
        levels = spec.levels
        values = [level.value for level in levels]

        if all(value is not None for value in values):
            # Values drive the silhouette directly: a descending series reads
            # as a funnel, an ascending one as a pyramid. `invert` does not
            # second-guess the data.
            largest = max(values)
            scaled = [
                WIDTH * max(value / largest, MIN_BAND_FRACTION) for value in values
            ]
            return [*scaled, scaled[-1] * 0.72]

        count = len(levels)
        step = (1.0 - NARROW) / count
        ramp = [WIDTH * (NARROW + step * i) for i in range(count + 1)]
        return list(reversed(ramp)) if spec.invert else ramp
