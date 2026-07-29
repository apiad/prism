"""How a Node is drawn. Shared by every archetype."""

from __future__ import annotations

import random
from dataclasses import dataclass

from tesserax import Container, Group
from tesserax.layout import ColumnLayout, RowLayout

from .icons import build_icon
from .nodes import Node
from .text import TextBlock
from .theme import Theme


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

    return Container(
        [body],
        padding=theme.geometry.pad,
        corner_radius=theme.geometry.radius,
        fill=theme.color("surface"),
        stroke=_border_color(node, theme),
        width=theme.geometry.stroke * (2 if node.emphasis == "strong" else 1),
    )
