import pytest
from pydantic import BaseModel

from prism.errors import UnknownArchetype
from prism.registry import get, names, register


class _Dummy(BaseModel):
    pass


class _Fake:
    name = "fake"
    spec_model = _Dummy

    def build(self, spec, ctx):
        raise NotImplementedError


def test_registered_archetype_is_retrievable():
    register(_Fake())
    assert get("fake").name == "fake"


def test_unknown_archetype_raises_with_suggestion():
    register(_Fake())
    with pytest.raises(UnknownArchetype) as excinfo:
        get("fkae")
    assert "fake" in str(excinfo.value)


def test_names_are_sorted():
    register(_Fake())
    assert names() == sorted(names())
