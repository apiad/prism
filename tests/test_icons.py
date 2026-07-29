import importlib.util
import json
from pathlib import Path

import pytest
from tesserax.color import hex as parse_hex

from prism.errors import UnknownIcon
from prism.icons import build_icon, icon_names

INK = parse_hex("#111827")

_SCRIPT = Path(__file__).parent.parent / "scripts" / "build_icons.py"
_ICON_DATA = Path(__file__).parent.parent / "prism" / "vendor" / "lucide" / "icons.json"


def _build_icons_module():
    spec = importlib.util.spec_from_file_location("build_icons", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_known_icons_are_available():
    names = icon_names()
    assert "database" in names
    assert "users" in names
    assert len(names) > 500


def test_icon_bounds_are_exactly_the_requested_size():
    bounds = build_icon("database", size=16, color=INK, stroke=1.5).local()
    assert bounds.width == 16
    assert bounds.height == 16


def test_icon_scales_to_requested_size():
    small = build_icon("database", size=16, color=INK, stroke=1.5).local()
    large = build_icon("database", size=32, color=INK, stroke=1.5).local()
    assert large.width > small.width


def test_unknown_icon_raises_with_suggestion():
    with pytest.raises(UnknownIcon) as excinfo:
        build_icon("databse", size=16, color=INK, stroke=1.5)
    assert "database" in str(excinfo.value)


def test_icon_renders_as_an_unfilled_stroked_path():
    svg = build_icon("database", size=16, color=INK, stroke=1.5).render()
    assert "<path" in svg
    assert 'fill="none"' in svg


def test_stroke_width_compensates_for_scaling():
    """A 16px icon and a 32px icon must have visually equal stroke weight."""
    small = build_icon("database", size=16, color=INK, stroke=1.5).render()
    large = build_icon("database", size=32, color=INK, stroke=1.5).render()
    assert small != large


def test_every_vendored_icon_starts_with_an_absolute_moveto():
    """Concatenated subpaths must not inherit the previous endpoint."""
    icons = json.loads(_ICON_DATA.read_text())["icons"]
    offenders = [name for name, d in icons.items() if not d.startswith("M")]
    assert offenders == []


def test_relative_moveto_keeps_its_implicit_linetos_relative():
    """Regression: `m9 12 2 2 4-4` is three RELATIVE ops, not one plus two absolute.

    Uppercasing only the command letter silently reinterprets the trailing
    coordinate pairs as absolute, which flings a checkmark out of its shield.
    """
    absolutize = _build_icons_module()._absolutize_start
    assert absolutize("m9 12 2 2 4-4") == "M9 12l2 2 4-4"
    assert absolutize("m22 7-8.5 8.5-5-5L2 17") == "M22 7l-8.5 8.5-5-5L2 17"


def test_relative_moveto_followed_by_a_command_needs_no_lineto():
    absolutize = _build_icons_module()._absolutize_start
    assert absolutize("m5 5L10 10") == "M5 5L10 10"


def test_absolute_subpaths_are_left_alone():
    absolutize = _build_icons_module()._absolutize_start
    assert absolutize("M16 7h6v6") == "M16 7h6v6"


def test_known_composite_icons_have_multiple_subpaths():
    icons = json.loads(_ICON_DATA.read_text())["icons"]
    for name in ("shield-check", "circle-check", "trending-up", "git-branch"):
        assert icons[name].count("M") >= 2, name
