"""Archetype registry — maps a spec `type` to its builder."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel
from tesserax import Group

from .errors import UnknownArchetype
from .nodebox import RenderContext


@runtime_checkable
class Archetype(Protocol):
    """A deterministic, network-free diagram builder for one spec `type`."""

    name: str
    spec_model: type[BaseModel]

    def build(self, spec: BaseModel, ctx: RenderContext) -> Group: ...


ARCHETYPES: dict[str, Archetype] = {}


def register(archetype: Archetype) -> None:
    ARCHETYPES[archetype.name] = archetype


def get(name: str) -> Archetype:
    if name not in ARCHETYPES:
        raise UnknownArchetype(name, ARCHETYPES)
    return ARCHETYPES[name]


def names() -> list[str]:
    return sorted(ARCHETYPES)
