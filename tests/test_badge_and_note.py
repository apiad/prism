"""Badge and note — the two Node fields that validated but drew nothing.

See `docs/specs/2026-07-31-node-badge-and-note-design.md`. The asymmetry these
tests protect: a badge lives *inside* the box and may grow it, a note lives
*outside* and must never move anything.
"""

import random
import re

import pytest
import yaml

from prism import render_str
from prism.errors import SpecError
from prism.nodebox import RenderContext, build_node_box, build_note, place_note
from prism.nodes import Node
from prism.registry import ARCHETYPES, get
from prism.theme import load_theme

NOTE_SUPPORTING = {"flow", "timeline"}


@pytest.fixture
def ctx():
    return RenderContext(theme=load_theme("default"), width=900, rng=random.Random(0))


def box_of(node: Node, ctx: RenderContext):
    return build_node_box(node, ctx)


def extent(shape):
    b = shape.local()
    return (b.x, b.y, b.width, b.height)


def arrows(svg: str) -> list[str]:
    return re.findall(r"<path[^>]*marker-end[^>]*>", svg)


# --- badge ------------------------------------------------------------------


def test_badge_reaches_the_svg(ctx):
    svg = box_of(Node(label="Ingest", badge="1"), ctx).render()
    assert ">1</text>" in svg


def test_no_badge_draws_no_badge(ctx):
    svg = box_of(Node(label="Ingest"), ctx).render()
    assert ">1</text>" not in svg


def test_badge_widens_the_box(ctx):
    plain = box_of(Node(label="Ingest"), ctx).local().width
    badged = box_of(Node(label="Ingest", badge="1"), ctx).local().width
    assert badged > plain


def test_badge_is_filled_with_the_node_accent(ctx):
    svg = box_of(Node(label="Ingest", badge="1", accent=2), ctx).render()
    assert str(ctx.theme.color(2)) in svg


def test_badge_letters_contrast_against_its_own_fill(ctx):
    """A badge is a filled pill, so its text is surface-coloured, not ink."""
    svg = box_of(Node(label="Ingest", badge="1"), ctx).render()
    letters = re.search(r'<text[^>]*fill="([^"]+)"[^>]*>1</text>', svg)
    assert letters and letters.group(1) == str(ctx.theme.color("surface"))


def test_badge_coexists_with_an_icon_and_a_sublabel(ctx):
    node = Node(label="Ingest", sublabel="S3 + Kafka", icon="database", badge="1")
    svg = box_of(node, ctx).render()
    assert ">1</text>" in svg
    assert ">Ingest</text>" in svg
    assert ">S3 + Kafka</text>" in svg


def test_a_badge_on_one_node_does_not_resize_another(ctx):
    """Badges grow their own box only — they are not a layout-wide setting."""
    plain = extent(box_of(Node(label="Ingest"), ctx))
    box_of(Node(label="Transform", badge="2"), ctx)
    assert extent(box_of(Node(label="Ingest"), ctx)) == plain


# --- note: the bounds invariant ---------------------------------------------


def test_a_note_never_changes_the_box_it_annotates(ctx):
    """The whole risk of this feature in one assertion.

    If a note grew the node box, `connect()` would attach arrows to the
    annotation's edge and every row would lose its middle alignment.
    """
    plain = extent(box_of(Node(label="Ingest"), ctx))
    noted = extent(box_of(Node(label="Ingest", note="runs nightly"), ctx))
    assert noted == plain


def test_notes_do_not_move_the_arrows_in_a_flow(ctx):
    bare = render_str("type: flow\nsteps: [{label: A}, {label: B}, {label: C}]")
    noted = render_str(
        "type: flow\nsteps: [{label: A, note: one}, {label: B, note: two}, {label: C}]"
    )
    assert arrows(noted) == arrows(bare)
    assert arrows(bare), "expected the bare flow to draw arrows at all"


# --- note: placement --------------------------------------------------------


def test_build_note_returns_nothing_for_an_unnoted_node(ctx):
    assert build_note(Node(label="Ingest"), ctx, 160) is None


def test_a_below_note_sits_under_the_box(ctx):
    node = Node(label="Ingest", note="runs nightly")
    box = box_of(node, ctx)
    note = place_note(node, box, ctx, "below")
    assert note.bounds().y >= box.bounds().y + box.bounds().height


def test_a_right_note_sits_beside_the_box(ctx):
    node = Node(label="Ingest", note="runs nightly")
    box = box_of(node, ctx)
    note = place_note(node, box, ctx, "right")
    assert note.bounds().x >= box.bounds().x + box.bounds().width


def test_a_below_note_wraps_to_the_width_of_its_box(ctx):
    node = Node(label="Ingest", note="runs nightly against the upstream bus snapshot")
    box = box_of(node, ctx)
    note = place_note(node, box, ctx, "below")
    assert note.local().width <= box.local().width


def test_notes_reach_the_svg_in_both_supporting_archetypes():
    """One word, so the assertion survives the box being narrow enough to wrap
    it — wrapping has its own test."""
    flow = render_str("type: flow\nsteps: [{label: A, note: nightly}]")
    timeline = render_str(
        "type: timeline\nevents: [{label: A, when: '2024', note: nightly}]"
    )
    assert ">nightly</text>" in flow
    assert ">nightly</text>" in timeline


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("type: flow\ndirection: right\nsteps: [{label: A, note: n}]", "below"),
        ("type: flow\ndirection: down\nsteps: [{label: A, note: n}]", "right"),
    ],
)
def test_flow_puts_the_note_away_from_the_arrows(spec, expected, ctx):
    """A note lands on the side the connectors do not use."""
    from prism.archetypes.flow.build import note_side
    from prism.archetypes.flow.schema import FlowSpec

    payload = {k: v for k, v in yaml.safe_load(spec).items() if k != "type"}
    assert note_side(FlowSpec.model_validate(payload)) == expected


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("type: timeline\norientation: horizontal\nevents: [{label: A}]", "below"),
        ("type: timeline\norientation: vertical\nevents: [{label: A}]", "right"),
    ],
)
def test_timeline_puts_the_note_away_from_the_spine(spec, expected):
    from prism.archetypes.timeline.build import note_side
    from prism.archetypes.timeline.schema import TimelineSpec

    payload = {k: v for k, v in yaml.safe_load(spec).items() if k != "type"}
    assert note_side(TimelineSpec.model_validate(payload)) == expected


def test_an_era_band_encloses_the_notes_of_the_events_it_spans(ctx):
    """A band edge slicing through a note reads as excluding it from the era."""
    from tesserax import Rect

    from prism.archetypes.timeline.schema import TimelineSpec

    spec = TimelineSpec.model_validate(
        {
            "events": [
                {"id": "a", "label": "Alpha", "note": "first"},
                {"id": "b", "label": "Beta", "note": "second"},
            ],
            "eras": [{"label": "Era", "span": ["a", "b"]}],
        }
    )
    group = get("timeline").build(spec, ctx)
    band = next(s for s in group.shapes if isinstance(s, Rect)).bounds()
    notes = [s for s in group.shapes if s not in (band,) and hasattr(s, "lines")]
    assert notes, "expected the timeline to have drawn its notes"

    for note in notes:
        edge = note.bounds()
        assert band.y + band.height >= edge.y + edge.height, (
            "the era band stops above its notes"
        )


# --- note: loud rejection ---------------------------------------------------


UNSUPPORTED = [
    ("cycle", "type: cycle\nsteps: [{label: A, note: n}, {label: B}, {label: C}]"),
    ("hub", "type: hub\ncenter: {label: C}\nspokes: [{label: A, note: n}, {label: B}]"),
    ("hierarchy", "type: hierarchy\nroot: {label: R, note: n}"),
    (
        "comparison",
        (
            "type: comparison\ncolumns:\n"
            "  - {header: {label: H1}, items: [{label: A, note: n}]}\n"
            "  - {header: {label: H2}, items: [{label: B}]}\n"
        ),
    ),
    (
        "matrix",
        (
            "type: matrix\nrows: [{label: R}]\ncolumns: [{label: C}]\n"
            "cells: [{row: R, column: C, label: A, note: n}]"
        ),
    ),
    ("pyramid", "type: pyramid\nlevels: [{label: A, note: n}, {label: B}]"),
    (
        "quadrant",
        (
            "type: quadrant\naxes:\n  x: {label: Cost}\n  y: {label: Value}\n"
            "items: [{label: A, note: n, x: 0.5, y: 0.5}]"
        ),
    ),
    ("stack", "type: stack\nlayers: [{label: A, note: n}]"),
]


@pytest.mark.parametrize(("name", "spec"), UNSUPPORTED, ids=[n for n, _ in UNSUPPORTED])
def test_a_note_on_an_archetype_that_cannot_place_it_is_an_error(name, spec):
    with pytest.raises(SpecError) as caught:
        render_str(spec)
    message = str(caught.value)
    assert name in message
    assert "note" in message


@pytest.mark.parametrize("name", sorted(ARCHETYPES))
def test_every_archetype_declares_whether_it_places_notes(name):
    """No getattr default — archetype #11 must decide, not inherit a silent no."""
    archetype = get(name)
    assert "supports_note" in vars(type(archetype)), (
        f"{name} does not declare supports_note; a new archetype must say "
        "whether it can place a marginal annotation"
    )
    assert archetype.supports_note is (name in NOTE_SUPPORTING)


def test_a_nested_note_is_caught_through_hierarchy_children():
    """hierarchy nests nodes, so the walk must recurse rather than scan a list."""
    spec = (
        "type: hierarchy\n"
        "root:\n"
        "  label: R\n"
        "  children:\n"
        "    - label: Child\n"
        "      note: buried deep\n"
    )
    with pytest.raises(SpecError, match="note"):
        render_str(spec)


# --- the drift guard should now let both fields back into the vocabulary -----


def test_badge_and_note_now_count_as_rendered_fields():
    from tests.test_docs import _rendered_node_fields

    assert {"badge", "note"} <= _rendered_node_fields()
