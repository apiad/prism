"""Schema for the `flow` archetype."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class FlowSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["right", "down"] = "right"
    steps: list[Node] = Field(min_length=1)
