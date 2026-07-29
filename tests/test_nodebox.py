import random

import pytest
from pydantic import ValidationError

from prism.nodebox import RenderContext, build_node_box
from prism.nodes import Node
from prism.theme import load_theme
from prism.typography import measure


@pytest.fixture
def ctx():
    return RenderContext(theme=load_theme("default"), width=900, rng=random.Random(0))


def test_node_requires_a_label():
    with pytest.raises(ValidationError):
        Node()


def test_node_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        Node(label="Ingest", colour="red")


def test_node_badge_is_length_limited():
    with pytest.raises(ValidationError):
        Node(label="Ingest", badge="toolong")


def test_box_contains_its_label(ctx):
    node = Node(label="Ingest")
    box = build_node_box(node, ctx)
    inner = box.local().width - 2 * ctx.theme.geometry.pad
    assert measure("Ingest", ctx.theme.size("label"), weight=700) <= inner


def test_long_label_wraps_instead_of_overflowing(ctx):
    node = Node(label="Ingest raw events from the upstream bus")
    box = build_node_box(node, ctx, max_width=120)
    assert box.local().width <= 120 + 2 * ctx.theme.geometry.pad


def test_sublabel_makes_the_box_taller(ctx):
    plain = build_node_box(Node(label="Ingest"), ctx).local().height
    with_sub = (
        build_node_box(Node(label="Ingest", sublabel="S3 + Kafka"), ctx).local().height
    )
    assert with_sub > plain


def test_icon_makes_the_box_wider(ctx):
    plain = build_node_box(Node(label="Ingest"), ctx).local().width
    with_icon = build_node_box(Node(label="Ingest", icon="database"), ctx).local().width
    assert with_icon > plain


def test_accent_index_colours_the_border(ctx):
    box = build_node_box(Node(label="Ingest", accent=1), ctx)
    assert str(box.stroke) == str(ctx.theme.color(1))


def test_muted_emphasis_uses_the_muted_token(ctx):
    box = build_node_box(Node(label="Ingest", emphasis="muted"), ctx)
    assert str(box.stroke) == str(ctx.theme.color("muted"))
