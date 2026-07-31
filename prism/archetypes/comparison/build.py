"""Side-by-side columns, optionally aligned against shared criteria."""

from __future__ import annotations

from tesserax import Group
from tesserax.base import Spacer
from tesserax.core import Shape
from tesserax.layout import GridLayout

from ...nodebox import RenderContext, build_node_box
from ...nodes import Node
from ...shapes import centered, label_block
from .schema import ComparisonSpec

CELL_WIDTH = 150.0


class ComparisonArchetype:
    name = "comparison"
    spec_model = ComparisonSpec
    supports_note = False

    def build(self, spec: ComparisonSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        columns = spec.columns
        cells: list[Shape] = []

        has_criteria = bool(spec.criteria)
        width = len(columns) + (1 if has_criteria else 0)

        if has_criteria:
            cells.append(Spacer(0, 0))

        for index, column in enumerate(columns):
            header = column.header.model_copy()
            if header.accent is None:
                header.accent = index
            header.emphasis = "strong"
            cells.append(build_node_box(header, ctx, max_width=CELL_WIDTH))

        rows = (
            len(spec.criteria)
            if has_criteria
            else max((len(column.items) for column in columns), default=0)
        )

        for row in range(rows):
            if has_criteria:
                caption = centered(
                    label_block(
                        Node(label=spec.criteria[row]),
                        ctx,
                        CELL_WIDTH,
                        role="sublabel",
                        color=theme.color("muted"),
                    )
                )
                cells.append(caption)
            for column in columns:
                if row < len(column.items):
                    cells.append(
                        build_node_box(column.items[row], ctx, max_width=CELL_WIDTH)
                    )
                else:
                    cells.append(Spacer(0, 0))

        return Group(
            [
                GridLayout(
                    cells,
                    cols=width,
                    gap=(theme.geometry.gap / 2, theme.geometry.gap / 2),
                )
            ]
        )
