"""Schema for the `matrix` archetype."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class Cell(Node):
    row: str
    column: str


class MatrixSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[Node] = Field(min_length=1)
    columns: list[Node] = Field(min_length=1)
    cells: list[Cell] = []
