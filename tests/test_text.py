from tesserax.color import hex as parse_hex

from prism.text import MeasuredText, TextBlock
from prism.typography import measure

INK = parse_hex("#111827")


def test_measured_text_bounds_match_measured_width():
    text = MeasuredText("Ingest", size=13, fill=INK)
    assert text.local().width == measure("Ingest", 13)


def test_measured_text_bounds_beat_the_tesserax_heuristic():
    # tesserax would give len * size * 0.6 == 5 * 12 * 0.6 == 36 for both.
    narrow = MeasuredText("lllll", size=12, fill=INK).local().width
    wide = MeasuredText("WWWWW", size=12, fill=INK).local().width
    assert narrow != wide


def test_measured_text_height_is_the_font_size():
    assert MeasuredText("Ingest", size=13, fill=INK).local().height == 13


def test_measured_text_emits_font_weight_and_family():
    svg = MeasuredText("Ingest", size=13, weight=700, fill=INK).render()
    assert 'font-weight="700"' in svg
    assert "Arial" in svg


def test_measured_text_escapes_markup_in_content():
    svg = MeasuredText("a<b & c", size=12, fill=INK).render()
    assert "&lt;b" in svg
    assert "&amp;" in svg


def test_text_block_splits_into_lines():
    block = TextBlock("Ingest raw events from the bus", 80, size=12, fill=INK)
    assert len(block.lines) > 1
    assert len(block.shapes) == len(block.lines)


def test_text_block_width_never_exceeds_its_budget():
    block = TextBlock("Ingest raw events from the bus", 80, size=12, fill=INK)
    assert block.local().width <= 80


def test_text_block_height_grows_with_line_count():
    one = TextBlock("Ingest", 500, size=12, fill=INK).local().height
    many = TextBlock("Ingest raw events from the bus", 80, size=12, fill=INK)
    assert many.local().height > one
