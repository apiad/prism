"""Declarative YAML to SVG diagrams."""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

import yaml
from pydantic import ValidationError
from tesserax.base import Group as _TGroup

from . import archetypes as _archetypes  # noqa: F401  (registers the catalog)
from .envelope import Envelope, load_spec
from .errors import PrismError, SpecError
from .frame import frame, with_accessibility
from .nodebox import RenderContext
from .registry import get
from .theme import load_theme

__version__ = "0.1.0.dev0"

__all__ = ["PrismError", "SpecError", "__version__", "render", "render_str"]

_ENVELOPE_KEYS = set(Envelope.model_fields)


def _seed(data: dict) -> int:
    canonical = yaml.safe_dump(data, sort_keys=True).encode()
    return int.from_bytes(hashlib.blake2b(canonical, digest_size=8).digest(), "big")


def render_str(source: str | Path) -> str:
    """Render a spec to an SVG string."""
    data = load_spec(source)
    envelope = Envelope.model_validate(data)
    archetype = get(envelope.type)

    payload = {k: v for k, v in data.items() if k not in _ENVELOPE_KEYS}
    try:
        spec = archetype.spec_model.model_validate(payload)
    except ValidationError as exc:
        raise SpecError(f"invalid '{envelope.type}' spec: {exc}") from exc

    theme = load_theme(envelope.theme, envelope.tokens or None)
    ctx = RenderContext(
        theme=theme, width=envelope.width, rng=random.Random(_seed(data))
    )

    # tesserax auto-attaches every constructed Shape to the innermost active
    # `with Group(...)`. That stack is a class-level global, so a caller who
    # renders inside their own canvas would otherwise collect our shapes.
    #
    # The guard must also cover SVG generation, not just construction: Line and
    # Arrow are lazy Components that build their Path when rendered, so calling
    # _repr_svg_ outside the guard leaks one Path per connector.
    saved, _TGroup.stack = _TGroup.stack, []
    try:
        canvas = frame(archetype.build(spec, ctx), envelope, ctx)
        svg = canvas._repr_svg_()
    finally:
        _TGroup.stack = saved

    return with_accessibility(svg, envelope)


def render(source: str | Path, out_path: str | Path) -> Path:
    """Render a spec and write it to `out_path`. Returns the path written."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_str(source), encoding="utf-8")
    return out
