"""Schema for the `comparison` archetype."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...nodes import Node


class Column(BaseModel):
    model_config = ConfigDict(extra="forbid")

    header: Node
    items: list[Node] = []


class ComparisonSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: list[str] = []
    columns: list[Column] = Field(min_length=2)

    @model_validator(mode="after")
    def _criteria_align(self) -> ComparisonSpec:
        if not self.criteria:
            return self
        expected = len(self.criteria)
        for index, column in enumerate(self.columns):
            if len(column.items) != expected:
                raise ValueError(
                    f"column {index} ({column.header.label!r}) has "
                    f"{len(column.items)} items but there are {expected} "
                    "criteria; with `criteria` set, every column must supply "
                    "one item per criterion, in the same order"
                )
        return self
