"""Schema for the `pyramid` archetype (invertible into a funnel)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class Level(Node):
    value: float | None = None


class PyramidSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invert: bool = False
    levels: list[Level] = Field(min_length=2)
