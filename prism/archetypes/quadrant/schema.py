"""Schema for the `quadrant` archetype."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class Axis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    low: str | None = None
    high: str | None = None


class Axes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: Axis
    y: Axis


class Item(Node):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


class QuadrantSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    axes: Axes
    quadrant_labels: list[str] = []
    items: list[Item] = Field(min_length=1)
