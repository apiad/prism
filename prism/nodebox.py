"""How a Node is drawn. Shared by every archetype."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from tesserax import Container, Group
from tesserax.core import Point, Shape
from tesserax.layout import ColumnLayout, RowLayout

from .icons import build_icon
from .nodes import Node
from .text import MeasuredText, TextBlock
from .theme import Theme

#: Width a right-hand note wraps to, before it starts competing with the label.
NOTE_COLUMN = 120.0

NoteSide = Literal["below", "right"]


@dataclass
class RenderContext:
    theme: Theme
    width: float
    rng: random.Random


def _border_color(node: Node, theme: Theme):
    if node.emphasis == "muted":
        return theme.color("muted")
    if node.accent is not None:
        return theme.color(node.accent)
    return theme.color("line")


def _badge_color(node: Node, theme: Theme):
    if node.emphasis == "muted":
        return theme.color("muted")
    if node.accent is not None:
        return theme.color(node.accent)
    return theme.color("ink")


def build_badge(node: Node, ctx: RenderContext) -> Container | None:
    """The short marker that rides inside the top-right of a node box.

    A filled pill, lettered in `surface` so it reads against its own fill. The
    schema caps a badge at four characters, so it never wraps and needs no
    overflow rule of its own.
    """
    if not node.badge:
        return None

    theme = ctx.theme
    fill = _badge_color(node, theme)
    return Container(
        [
            MeasuredText(
                node.badge,
                size=theme.size("badge"),
                fill=theme.color("surface"),
                family=theme.typography.family,
                weight=theme.weight("badge"),
            )
        ],
        padding=theme.geometry.pad / 3,
        corner_radius=theme.geometry.radius,
        fill=fill,
        stroke=fill,
        width=0,
    )


def build_node_box(node: Node, ctx: RenderContext, max_width: float = 160) -> Container:
    theme = ctx.theme
    ink = theme.color("ink") if node.emphasis != "muted" else theme.color("muted")

    stack: list = [
        TextBlock(
            node.label,
            max_width,
            size=theme.size("label"),
            fill=ink,
            family=theme.typography.family,
            weight=theme.weight("label"),
            line_height=theme.typography.line_height,
        )
    ]

    if node.sublabel:
        stack.append(
            TextBlock(
                node.sublabel,
                max_width,
                size=theme.size("sublabel"),
                fill=theme.color("muted"),
                family=theme.typography.family,
                weight=theme.weight("sublabel"),
                line_height=theme.typography.line_height,
            )
        )

    body: Group = ColumnLayout(stack, align="middle", gap=theme.geometry.gap / 6)

    if node.icon:
        glyph = build_icon(
            node.icon,
            size=theme.size("label") * 1.4,
            color=ink,
            stroke=theme.geometry.stroke,
        )
        body = RowLayout([glyph, body], align="middle", gap=theme.geometry.pad / 2)

    badge = build_badge(node, ctx)
    if badge is not None:
        # A flow-layout sibling rather than an overlay: the box grows to hold
        # the pill, so its bounds stay honest and `connect()` keeps attaching
        # arrows to the real border.
        body = RowLayout([body, badge], align="start", gap=theme.geometry.pad / 2)

    return Container(
        [body],
        padding=theme.geometry.pad,
        corner_radius=theme.geometry.radius,
        fill=theme.color("surface"),
        stroke=_border_color(node, theme),
        width=theme.geometry.stroke * (2 if node.emphasis == "strong" else 1),
    )


def build_note(node: Node, ctx: RenderContext, max_width: float) -> TextBlock | None:
    """The marginal annotation for a node, unparented and unpositioned.

    Deliberately *not* part of the node box. Folding it in would grow the box
    downward, and every archetype reads those bounds to align rows and to find
    the edge an arrow should land on.
    """
    if not node.note:
        return None

    theme = ctx.theme
    return TextBlock(
        node.note,
        max_width,
        size=theme.size("note"),
        fill=theme.color("muted"),
        family=theme.typography.family,
        weight=theme.weight("note"),
        line_height=theme.typography.line_height,
        anchor="start",
    )


def place_note(
    node: Node, box: Shape, ctx: RenderContext, side: NoteSide
) -> TextBlock | None:
    """Build a node's note and move it into the margin beside its box.

    `side` is chosen by the archetype as the direction its connective tissue
    does *not* use — below a left-to-right spine, right of a top-down one.

    Positions against `box.bounds()`, so the result belongs in the same group
    as the layout holding the boxes, exactly like a connector.
    """
    frame = box.bounds()
    width = frame.width if side == "below" else NOTE_COLUMN
    note = build_note(node, ctx, width)
    if note is None:
        return None

    gap = ctx.theme.geometry.pad / 2
    extent = note.local()
    if side == "below":
        centre = Point(
            frame.x + extent.width / 2,
            frame.y + frame.height + gap + extent.height / 2,
        )
    else:
        centre = Point(
            frame.x + frame.width + gap + extent.width / 2,
            frame.y + frame.height / 2,
        )

    note.move_to(centre, "center")
    return note
