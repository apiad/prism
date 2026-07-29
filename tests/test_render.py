import pytest
import tesserax

import prism
from prism.errors import SpecError, UnknownArchetype

SPEC = """
type: flow
title: Ingestion
caption: "Source: internal"
steps:
  - label: Ingest
    icon: database
  - label: Verify
  - label: Publish
"""


def test_render_str_emits_svg():
    svg = prism.render_str(SPEC)
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")


def test_render_writes_a_file(tmp_path):
    out = prism.render(SPEC, tmp_path / "d.svg")
    assert out.exists()
    assert out.read_text().startswith("<svg")


def test_title_and_caption_appear_in_the_output():
    svg = prism.render_str(SPEC)
    assert "Ingestion" in svg
    assert "internal" in svg


def test_output_carries_accessibility_metadata():
    svg = prism.render_str(SPEC)
    assert 'role="img"' in svg
    assert "<title>" in svg
    assert "<desc>" in svg


def test_rendering_is_deterministic():
    assert prism.render_str(SPEC) == prism.render_str(SPEC)


def test_unknown_archetype_raises():
    with pytest.raises(UnknownArchetype):
        prism.render_str("type: flowchart\nsteps: [{label: A}]\n")


def test_invalid_payload_raises_spec_error():
    with pytest.raises(SpecError):
        prism.render_str("type: flow\nsteps: []\n")


def test_unknown_field_raises_spec_error():
    with pytest.raises(SpecError):
        prism.render_str("type: flow\nsteps: [{label: A, colour: red}]\n")


def test_inline_token_overrides_apply():
    # tesserax serialises colours as rgba(), not hex.
    svg = prism.render_str(SPEC + "tokens:\n  palette.ink: '#ff0000'\n")
    assert "rgba(255,0,0" in svg


def test_render_does_not_leak_into_a_users_canvas():
    """tesserax's Group.stack is global; prism must not attach shapes to it."""
    with tesserax.Canvas() as canvas:
        prism.render_str(SPEC)
    assert canvas.shapes == []


def test_output_paints_the_theme_surface():
    """A transparent SVG makes a dark theme's light ink unreadable."""
    svg = prism.render_str(SPEC.replace("type:", "theme: dark\ntype:", 1))
    # The dark surface must appear before any content.
    assert "rgba(15,23,42" in svg.split("<title>")[0] + svg[:2000]


def test_light_theme_also_paints_a_background():
    svg = prism.render_str(SPEC)
    assert "rgba(255,255,255" in svg


def test_diagram_displays_itself_as_svg():
    """Quarto and Jupyter embed whatever _repr_svg_ returns."""
    result = prism.diagram(SPEC)
    assert result._repr_svg_().startswith("<svg")
    assert result.svg == prism.render_str(SPEC)


def test_diagram_saves_itself(tmp_path):
    out = prism.diagram(SPEC).save(tmp_path / "nested" / "d.svg")
    assert out.read_text().startswith("<svg")


def test_diagram_repr_is_not_the_whole_svg():
    assert repr(prism.diagram(SPEC)).startswith("<prism.Diagram")
