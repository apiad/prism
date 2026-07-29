"""Cross-archetype guarantees, applied to every registered archetype."""

from __future__ import annotations

import pytest

import prism
from prism.registry import names
from prism.theme import bundled_themes, load_theme

from .samples import SAMPLES


def test_every_registered_archetype_has_a_sample():
    """A new archetype without a sample is an untested archetype."""
    assert sorted(SAMPLES) == names()


@pytest.mark.parametrize("archetype", sorted(SAMPLES))
def test_sample_renders_to_svg(archetype):
    svg = prism.render_str(SAMPLES[archetype])
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")


@pytest.mark.parametrize("archetype", sorted(SAMPLES))
def test_sample_render_is_deterministic(archetype):
    spec = SAMPLES[archetype]
    assert prism.render_str(spec) == prism.render_str(spec)


@pytest.mark.parametrize("archetype", sorted(SAMPLES))
def test_sample_has_non_degenerate_size(archetype):
    """A diagram that collapses to a sliver is a layout failure, not a render."""
    svg = prism.render_str(SAMPLES[archetype])
    header = svg.split(">", 1)[0]
    width = float(header.split('width="')[1].split('"')[0])
    height = float(header.split('height="')[1].split('"')[0])
    assert width > 80
    assert height > 60


@pytest.mark.parametrize("archetype", sorted(SAMPLES))
@pytest.mark.parametrize("theme", bundled_themes())
def test_sample_renders_in_every_theme(archetype, theme):
    spec = SAMPLES[archetype].replace("type:", f"theme: {theme}\ntype:", 1)
    assert prism.render_str(spec).startswith("<svg")


@pytest.mark.parametrize("theme", bundled_themes())
def test_bundled_theme_is_valid(theme):
    loaded = load_theme(theme)
    assert loaded.name == theme
    assert len(loaded.palette.ramp) >= 3
