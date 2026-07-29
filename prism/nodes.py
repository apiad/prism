"""The rich node every archetype shares."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    label: str
    sublabel: str | None = None
    icon: str | None = None
    badge: str | None = Field(default=None, max_length=4)
    accent: int | str | None = None
    emphasis: Literal["strong", "normal", "muted"] = "normal"
    note: str | None = None


class GroupSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    members: list[str] = Field(min_length=1)
    accent: int | str | None = None


class Link(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    source: str = Field(alias="from")
    target: str = Field(alias="to")
    label: str | None = None
    style: Literal["solid", "dashed", "dotted"] = "solid"
    kind: Literal["forward", "back", "bidirectional"] = "forward"
