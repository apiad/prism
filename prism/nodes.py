"""The rich node every archetype shares."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Literal

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


def walk_nodes(value: Any) -> Iterator[Node]:
    """Every Node reachable in a validated spec, however deeply nested.

    A tree recurses through `children` and a comparison hides its nodes one
    model down, so a scan of the spec's own lists would miss them.
    """
    if isinstance(value, Node):
        yield value
    if isinstance(value, BaseModel):
        for name in type(value).model_fields:
            yield from walk_nodes(getattr(value, name))
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_nodes(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_nodes(item)
