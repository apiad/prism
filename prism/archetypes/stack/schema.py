"""Schema for the `stack` archetype."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class Layer(Node):
    side: str | None = None


class StackSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order: Literal["top_down", "bottom_up"] = "top_down"
    layers: list[Layer] = Field(min_length=1)
