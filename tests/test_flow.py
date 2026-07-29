import random

import pytest
from pydantic import ValidationError

from prism.archetypes.flow.schema import FlowSpec
from prism.nodebox import RenderContext
from prism.registry import get
from prism.theme import load_theme


@pytest.fixture
def ctx():
    return RenderContext(theme=load_theme("default"), width=900, rng=random.Random(0))


def test_flow_is_registered():
    assert get("flow").name == "flow"


def test_flow_requires_at_least_one_step():
    with pytest.raises(ValidationError):
        FlowSpec(steps=[])


def test_flow_defaults_to_left_to_right():
    assert FlowSpec(steps=[{"label": "A"}]).direction == "right"


def test_horizontal_flow_is_wider_than_tall(ctx):
    spec = FlowSpec(steps=[{"label": "A"}, {"label": "B"}, {"label": "C"}])
    bounds = get("flow").build(spec, ctx).local()
    assert bounds.width > bounds.height


def test_vertical_flow_is_taller_than_wide(ctx):
    spec = FlowSpec(
        direction="down", steps=[{"label": "A"}, {"label": "B"}, {"label": "C"}]
    )
    bounds = get("flow").build(spec, ctx).local()
    assert bounds.height > bounds.width


def test_flow_draws_one_connector_between_each_pair(ctx):
    spec = FlowSpec(steps=[{"label": "A"}, {"label": "B"}, {"label": "C"}])
    svg = get("flow").build(spec, ctx).render()
    assert svg.count("marker-end") == 2


def test_single_step_flow_has_no_connectors(ctx):
    spec = FlowSpec(steps=[{"label": "A"}])
    assert "marker-end" not in get("flow").build(spec, ctx).render()


def test_steps_grow_the_diagram(ctx):
    two = get("flow").build(FlowSpec(steps=[{"label": "A"}, {"label": "B"}]), ctx)
    four = get("flow").build(
        FlowSpec(
            steps=[{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}]
        ),
        ctx,
    )
    assert four.local().width > two.local().width
