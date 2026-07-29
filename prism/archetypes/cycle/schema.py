"""Schema for the `cycle` archetype."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class CycleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["clockwise", "counterclockwise"] = "clockwise"
    center: Node | None = None
    steps: list[Node] = Field(min_length=2)
