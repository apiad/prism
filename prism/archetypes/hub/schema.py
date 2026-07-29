"""Schema for the `hub` archetype."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class HubSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    center: Node
    spokes: list[Node] = Field(min_length=2)
    ring: bool = False
