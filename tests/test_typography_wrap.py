from prism.typography import measure, wrap


def test_short_text_stays_on_one_line():
    assert wrap("Ingest", 500, 12) == ["Ingest"]


def test_empty_text_yields_a_single_empty_line():
    assert wrap("", 500, 12) == [""]


def test_text_breaks_at_whitespace():
    lines = wrap("Ingest raw events from the bus", 80, 12)
    assert len(lines) > 1
    assert all(" " not in line[:1] for line in lines)


def test_no_wrapped_line_exceeds_the_budget():
    budget = 80
    for line in wrap("Ingest raw events from the upstream bus", budget, 12):
        assert measure(line, 12) <= budget


def test_a_single_oversized_word_is_hard_broken():
    lines = wrap("Supercalifragilisticexpialidocious", 40, 12)
    assert len(lines) > 1
    for line in lines:
        assert measure(line, 12) <= 40


def test_existing_newlines_are_honoured_as_hard_breaks():
    assert wrap("Ingest\nVerify", 500, 12) == ["Ingest", "Verify"]


def test_runs_of_whitespace_collapse():
    assert wrap("Ingest    events", 500, 12) == ["Ingest events"]
