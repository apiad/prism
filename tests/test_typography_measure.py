import pytest

from prism.errors import PrismError
from prism.typography import FAMILIES, load_metrics, measure


def test_families_are_exactly_the_three_supported_stacks():
    assert set(FAMILIES) == {"grotesque", "serif", "mono"}
    assert "Arial" in FAMILIES["grotesque"]


def test_empty_string_measures_zero():
    assert measure("", 12) == 0.0


def test_measure_scales_linearly_with_size():
    assert measure("Ingest", 24) == pytest.approx(measure("Ingest", 12) * 2)


def test_narrow_text_measures_less_than_wide_text():
    assert measure("lllll", 12) < measure("WWWWW", 12)


def test_mono_measures_purely_by_length():
    five = measure("iiiii", 12, family="mono")
    assert measure("WWWWW", 12, family="mono") == pytest.approx(five)


def test_bold_is_wider_than_regular_for_the_same_string():
    assert measure("Ingest", 12, weight=700) > measure("Ingest", 12, weight=400)


def test_unknown_glyph_falls_back_to_default_advance():
    metrics = load_metrics("grotesque", 400)
    expected = metrics.default_advance * 12 / metrics.units_per_em
    assert measure("中", 12) == pytest.approx(expected)


def test_unknown_family_raises_prism_error():
    with pytest.raises(PrismError):
        measure("x", 12, family="comic")


def test_unknown_weight_raises_prism_error():
    with pytest.raises(PrismError):
        measure("x", 12, weight=600)
