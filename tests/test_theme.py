import pytest
from tesserax.color import hex as parse_hex

from prism.errors import PrismError
from prism.theme import Theme, load_theme


def test_default_theme_loads():
    theme = load_theme("default")
    assert isinstance(theme, Theme)
    assert theme.name == "default"
    assert len(theme.palette.ramp) >= 3


def test_color_resolves_a_ramp_index():
    theme = load_theme("default")
    assert theme.color(0) == parse_hex(theme.palette.ramp[0])


def test_ramp_index_wraps_around():
    theme = load_theme("default")
    assert theme.color(len(theme.palette.ramp)) == theme.color(0)


def test_color_resolves_a_palette_token_name():
    theme = load_theme("default")
    assert theme.color("muted") == parse_hex(theme.palette.muted)


def test_color_defaults_to_ink():
    theme = load_theme("default")
    assert theme.color(None) == parse_hex(theme.palette.ink)


def test_unknown_token_name_raises():
    theme = load_theme("default")
    with pytest.raises(PrismError):
        theme.color("accnt")


def test_dotted_overrides_apply():
    theme = load_theme("default", {"palette.ink": "#0b1020", "geometry.radius": 2})
    assert theme.palette.ink == "#0b1020"
    assert theme.geometry.radius == 2


def test_unknown_theme_name_raises():
    with pytest.raises(PrismError):
        load_theme("defualt")


def test_unknown_override_path_raises():
    with pytest.raises(PrismError):
        load_theme("default", {"palette.inc": "#000000"})


def test_weight_other_than_400_or_700_is_rejected():
    with pytest.raises(PrismError):
        load_theme("default", {"typography.weight": {"label": 600}})
