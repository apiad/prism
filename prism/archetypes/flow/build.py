"""Compose a linear flow of steps connected by arrows."""

from __future__ import annotations

from tesserax import Group
from tesserax.layout import ColumnLayout, RowLayout

from ...connectors import connect
from ...nodebox import NoteSide, RenderContext, build_node_box, place_note
from .schema import FlowSpec


def note_side(spec: FlowSpec) -> NoteSide:
    """Notes go where the arrows do not: under a spine that runs sideways."""
    return "below" if spec.direction == "right" else "right"


class FlowArchetype:
    name = "flow"
    spec_model = FlowSpec
    supports_note = True

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

        side = note_side(spec)
        notes = [
            note
            for step, box in zip(spec.steps, boxes, strict=True)
            if (note := place_note(step, box, ctx, side)) is not None
        ]

        return Group([spine, *connectors, *notes])
