"""Themes are data — a token set, never code."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from tesserax.color import Color
from tesserax.color import hex as parse_hex

from .errors import PrismError, SpecError, UnknownToken
from .typography import FAMILIES, WEIGHTS

_THEMES_DIR = Path(__file__).parent / "themes"


class Palette(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface: str
    ink: str
    muted: str
    line: str
    ramp: list[str] = Field(min_length=3)
    ok: str
    warn: str
    bad: str


class Typography(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str = "grotesque"
    scale: dict[str, float]
    weight: dict[str, int]
    line_height: float = 1.35

    @field_validator("family")
    @classmethod
    def _known_family(cls, value: str) -> str:
        if value not in FAMILIES:
            raise UnknownToken(value, FAMILIES)
        return value

    @field_validator("weight")
    @classmethod
    def _supported_weights(cls, value: dict[str, int]) -> dict[str, int]:
        for role, weight in value.items():
            if weight not in WEIGHTS:
                raise PrismError(
                    f"typography.weight.{role} is {weight!r}; prism supports "
                    "only 400 and 700, the weights whose metrics are vendored"
                )
        return value


class Geometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    radius: float = 6
    stroke: float = 1.5
    gap: float = 24
    pad: float = 12
    arrow: Literal["standard", "thin", "block"] = "standard"


class Theme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    palette: Palette
    typography: Typography
    geometry: Geometry
    # Only `clean` in v1. tesserax's Sketch flattens a shape tree but drops
    # each group's own transform (see the comment in tesserax/sketch.py), so a
    # sketched prism diagram collapses every nested layout onto the origin.
    # Accepting the token without honouring it would be worse than refusing it.
    texture: Literal["clean"] = "clean"

    def color(self, ref: int | str | None = None) -> Color:
        if ref is None:
            return parse_hex(self.palette.ink)
        if isinstance(ref, int):
            ramp = self.palette.ramp
            return parse_hex(ramp[ref % len(ramp)])
        named = {
            k: v for k, v in self.palette.model_dump().items() if isinstance(v, str)
        }
        if ref not in named:
            raise UnknownToken(ref, named)
        return parse_hex(named[ref])

    def size(self, role: str) -> float:
        if role not in self.typography.scale:
            raise UnknownToken(role, self.typography.scale)
        return self.typography.scale[role]

    def weight(self, role: str) -> int:
        return self.typography.weight.get(role, 400)


def _dotted_paths(data: dict[str, Any], prefix: str = "") -> list[str]:
    paths: list[str] = []
    for key, value in data.items():
        path = f"{prefix}{key}"
        paths.append(path)
        if isinstance(value, dict):
            paths.extend(_dotted_paths(value, f"{path}."))
    return paths


def _apply_overrides(data: dict[str, Any], overrides: dict[str, Any]) -> dict:
    known = _dotted_paths(data)
    for dotted, value in overrides.items():
        target = data
        *parents, leaf = dotted.split(".")
        for part in parents:
            if part not in target or not isinstance(target[part], dict):
                raise UnknownToken(dotted, known)
            target = target[part]
        if leaf not in target:
            raise UnknownToken(dotted, known)
        target[leaf] = value
    return data


def bundled_themes() -> list[str]:
    return sorted(p.stem for p in _THEMES_DIR.glob("*.yaml"))


def load_theme(ref: str = "default", overrides: dict[str, Any] | None = None) -> Theme:
    path = Path(ref)
    if not path.suffix:
        path = _THEMES_DIR / f"{ref}.yaml"
        if not path.exists():
            raise UnknownToken(ref, bundled_themes())
    elif not path.exists():
        raise PrismError(f"theme file not found: {ref}")

    data = yaml.safe_load(path.read_text())
    if overrides:
        data = _apply_overrides(data, overrides)

    try:
        return Theme.model_validate(data)
    except ValidationError as exc:
        # pydantic wraps validator exceptions, so re-raise as our own type.
        raise SpecError(f"invalid theme {ref!r}: {exc}") from exc
