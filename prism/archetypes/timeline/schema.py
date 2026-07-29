"""Schema for the `timeline` archetype."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class Event(Node):
    when: str | None = None


class Era(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    span: tuple[str, str]
    accent: int | str | None = None


class TimelineSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    orientation: Literal["horizontal", "vertical"] = "horizontal"
    events: list[Event] = Field(min_length=1)
    eras: list[Era] = []
