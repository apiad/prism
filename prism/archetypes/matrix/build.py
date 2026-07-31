"""Row x column headers with sparse cell content."""

from __future__ import annotations

from tesserax import Group
from tesserax.base import Spacer
from tesserax.core import Shape
from tesserax.layout import GridLayout

from ...errors import SpecError
from ...nodebox import RenderContext, build_node_box
from ...shapes import centered, label_block
from .schema import MatrixSpec

CELL_WIDTH = 130.0


class MatrixArchetype:
    name = "matrix"
    spec_model = MatrixSpec
    supports_note = False

    def build(self, spec: MatrixSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        row_keys = [node.id or node.label for node in spec.rows]
        column_keys = [node.id or node.label for node in spec.columns]

        lookup: dict[tuple[str, str], Shape] = {}
        for cell in spec.cells:
            if cell.row not in row_keys:
                raise SpecError(
                    f"cell references unknown row {cell.row!r}; known rows: {row_keys}"
                )
            if cell.column not in column_keys:
                raise SpecError(
                    f"cell references unknown column {cell.column!r}; "
                    f"known columns: {column_keys}"
                )
            lookup[cell.row, cell.column] = build_node_box(
                cell, ctx, max_width=CELL_WIDTH
            )

        cells: list[Shape] = [Spacer(0, 0)]
        for column in spec.columns:
            cells.append(
                centered(label_block(column, ctx, CELL_WIDTH, color=theme.color("ink")))
            )

        for row, row_key in zip(spec.rows, row_keys, strict=True):
            cells.append(
                centered(label_block(row, ctx, CELL_WIDTH, color=theme.color("ink")))
            )
            for column_key in column_keys:
                cells.append(lookup.get((row_key, column_key)) or Spacer(0, 0))

        return Group(
            [
                GridLayout(
                    cells,
                    cols=len(spec.columns) + 1,
                    gap=(theme.geometry.gap / 2, theme.geometry.gap / 2),
                )
            ]
        )
