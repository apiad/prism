"""Steps arranged on a ring, joined by arcs."""

from __future__ import annotations

import math

from tesserax import Arrow, Group
from tesserax.core import Point, Shape

from ...connectors import MARKER_ID
from ...nodebox import RenderContext, build_node_box
from ...shapes import at, text_stack
from .schema import CycleSpec

MIN_RADIUS = 120.0
CURVATURE = 0.18


class CycleArchetype:
    name = "cycle"
    spec_model = CycleSpec

    def build(self, spec: CycleSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        steps = spec.steps
        count = len(steps)

        boxes = [build_node_box(step, ctx, max_width=130) for step in steps]

        # The ring has to be wide enough that neighbouring boxes do not touch.
        widest = max(b.local().width for b in boxes)
        tallest = max(b.local().height for b in boxes)
        circumference = count * (widest + theme.geometry.gap)
        radius = max(MIN_RADIUS, circumference / (2 * math.pi), widest, tallest)

        sign = 1.0 if spec.direction == "clockwise" else -1.0
        angles = [-math.pi / 2 + sign * (2 * math.pi * i / count) for i in range(count)]

        for box, angle in zip(boxes, angles, strict=True):
            at(box, radius * math.cos(angle), radius * math.sin(angle))

        shapes: list[Shape] = list(boxes)

        if spec.center is not None:
            hub = text_stack(spec.center, ctx, radius * 1.1)
            at(hub, 0, 0)
            shapes.append(hub)

        # Arcs run on the ring itself, backed off by each box's angular radius
        # so they emerge from outside the box rather than under it.
        arcs: list[Shape] = []
        for index in range(count):
            start, end = angles[index], angles[(index + 1) % count]
            pad_start = self._angular_padding(boxes[index], radius)
            pad_end = self._angular_padding(boxes[(index + 1) % count], radius)
            a0 = start + sign * pad_start
            a1 = end - sign * pad_end
            arcs.append(
                Arrow(
                    Point(radius * math.cos(a0), radius * math.sin(a0)),
                    Point(radius * math.cos(a1), radius * math.sin(a1)),
                    curvature=CURVATURE * sign,
                    stroke=theme.color("muted"),
                    width=theme.geometry.stroke,
                    marker_end=MARKER_ID,
                )
            )

        return Group([*arcs, *shapes])

    @staticmethod
    def _angular_padding(box: Shape, radius: float) -> float:
        bounds = box.local()
        reach = math.hypot(bounds.width, bounds.height) / 2
        return min(math.atan2(reach, radius) * 1.15, math.pi / 3)
