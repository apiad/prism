"""Compose a linear flow of steps connected by arrows."""

from __future__ import annotations

from tesserax import Group
from tesserax.layout import ColumnLayout, RowLayout

from ...connectors import connect
from ...nodebox import RenderContext, build_node_box
from .schema import FlowSpec


class FlowArchetype:
    name = "flow"
    spec_model = FlowSpec

    def build(self, spec: FlowSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        boxes = [build_node_box(step, ctx) for step in spec.steps]

        if spec.direction == "right":
            spine = RowLayout(boxes, align="middle", gap=theme.geometry.gap)
            tail, head = "right", "left"
        else:
            spine = ColumnLayout(boxes, align="middle", gap=theme.geometry.gap)
            tail, head = "bottom", "top"

        connectors = [
            connect(boxes[i], boxes[i + 1], tail, head, theme)
            for i in range(len(boxes) - 1)
        ]

        return Group([spine, *connectors])
