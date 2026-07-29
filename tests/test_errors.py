import pytest

from prism.errors import PrismError, UnknownIcon, suggest


def test_suggest_ranks_close_matches_first():
    assert suggest("databse", ["database", "data-flow", "shield"])[0] == "database"


def test_suggest_returns_empty_when_nothing_is_close():
    assert suggest("zzzzzz", ["database", "shield"]) == []


def test_unknown_icon_message_names_value_and_suggestions():
    err = UnknownIcon("databse", ["database", "shield"])
    message = str(err)
    assert "databse" in message
    assert "database" in message
    assert isinstance(err, PrismError)


def test_unknown_icon_message_survives_no_suggestions():
    message = str(UnknownIcon("zzzzzz", ["database", "shield"]))
    assert "zzzzzz" in message
    assert "2 known icons" in message


def test_prism_error_is_catchable_as_exception():
    with pytest.raises(PrismError):
        raise UnknownIcon("x", ["database"])
