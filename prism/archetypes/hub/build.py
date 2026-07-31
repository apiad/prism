"""A centre with radial spokes."""

from __future__ import annotations

import math

from tesserax import Group, Line
from tesserax.core import Point, Shape

from ...nodebox import RenderContext, build_node_box
from ...shapes import at
from .schema import HubSpec

MIN_RADIUS = 130.0


class HubArchetype:
    name = "hub"
    spec_model = HubSpec
    supports_note = False

    def build(self, spec: HubSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        centre_node = spec.center.model_copy()
        centre_node.emphasis = "strong"
        if centre_node.accent is None:
            # Otherwise the hub inherits the faint `line` border, which reads
            # as less important than its own spokes.
            centre_node.accent = "ink"
        centre = build_node_box(centre_node, ctx, max_width=140)
        at(centre, 0, 0)

        spokes = [build_node_box(node, ctx, max_width=120) for node in spec.spokes]
        count = len(spokes)

        widest = max(s.local().width for s in spokes)
        radius = max(
            MIN_RADIUS,
            count * (widest + theme.geometry.gap) / (2 * math.pi),
            centre.local().width / 2 + widest / 2 + theme.geometry.gap,
        )

        angles = [-math.pi / 2 + 2 * math.pi * i / count for i in range(count)]
        for spoke, angle in zip(spokes, angles, strict=True):
            at(spoke, radius * math.cos(angle), radius * math.sin(angle))

        # Draw the leg from the hub's rim to the spoke's rim, not centre to
        # centre, so the line never runs underneath either box.
        legs: list[Shape] = []
        for spoke, angle in zip(spokes, angles, strict=True):
            direction = Point(math.cos(angle), math.sin(angle))
            start = self._rim(centre.local(), direction)
            end_offset = self._rim(spoke.local(), Point(-direction.x, -direction.y))
            legs.append(
                Line(
                    Point(start.x, start.y),
                    Point(
                        radius * direction.x + end_offset.x,
                        radius * direction.y + end_offset.y,
                    ),
                    stroke=theme.color("line"),
                    width=theme.geometry.stroke,
                )
            )

        ring: list[Shape] = []
        if spec.ring:
            for index in range(count):
                a, b = angles[index], angles[(index + 1) % count]
                ring.append(
                    Line(
                        Point(radius * math.cos(a), radius * math.sin(a)),
                        Point(radius * math.cos(b), radius * math.sin(b)),
                        curvature=0.2,
                        stroke=theme.color("line"),
                        width=theme.geometry.stroke,
                    )
                )

        return Group([*ring, *legs, centre, *spokes])

    @staticmethod
    def _rim(bounds, direction: Point) -> Point:
        """Where a ray from the centre of `bounds` leaves its rectangle."""
        half_w, half_h = bounds.width / 2, bounds.height / 2
        if abs(direction.x) < 1e-9:
            return Point(0, math.copysign(half_h, direction.y))
        if abs(direction.y) < 1e-9:
            return Point(math.copysign(half_w, direction.x), 0)
        scale = min(half_w / abs(direction.x), half_h / abs(direction.y))
        return Point(direction.x * scale, direction.y * scale)
