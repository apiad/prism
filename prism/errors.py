"""Exceptions written to be read by a model, not only by a human."""

from __future__ import annotations

import difflib
from collections.abc import Iterable


def suggest(value: str, candidates: Iterable[str], n: int = 3) -> list[str]:
    """Return the closest candidates to `value`, best first."""
    return difflib.get_close_matches(value, list(candidates), n=n, cutoff=0.6)


class PrismError(Exception):
    """Base class for every error prism raises on purpose."""


class SpecError(PrismError):
    """The spec failed validation against its archetype's schema."""


class _UnknownName(PrismError):
    noun = "value"

    def __init__(self, value: str, candidates: Iterable[str]) -> None:
        known = list(candidates)
        hits = suggest(value, known)
        if hits:
            tail = f"did you mean: {', '.join(hits)}?"
        else:
            tail = f"no close match among {len(known)} known {self.noun}s"
        super().__init__(f"unknown {self.noun} {value!r} — {tail}")
        self.value = value
        self.candidates = known


class UnknownArchetype(_UnknownName):
    noun = "archetype"


class UnknownIcon(_UnknownName):
    noun = "icon"


class UnknownToken(_UnknownName):
    noun = "token"
