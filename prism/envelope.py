"""The common shell every prism spec shares."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from .errors import SpecError


class Envelope(BaseModel):
    # Archetype payload keys live alongside these, so extras are ignored here.
    model_config = ConfigDict(extra="ignore")

    type: str
    theme: str = "default"
    title: str | None = None
    subtitle: str | None = None
    caption: str | None = None
    width: float = 900
    tokens: dict[str, Any] = {}


def load_spec(source: str | Path) -> dict:
    """Load a spec from a file path or from raw YAML text."""
    text = str(source)
    if len(text) < 4096 and os.path.exists(text):
        text = Path(text).read_text()

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SpecError(f"spec is not valid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise SpecError(
            "a prism spec must be a YAML mapping with a top-level 'type' field"
        )
    if "type" not in data:
        raise SpecError(
            "a prism spec needs a top-level 'type' field naming the archetype"
        )
    return data
