"""Small geometry helpers shared by archetypes.

`Shape.move_to` is defined in terms of `Shape.anchor`, which resolves through
the parent chain. These helpers therefore only work on *unparented* shapes —
position first, group afterwards.
"""

from __future__ import annotations

from tesserax import Group, Path, Rect
from tesserax.color import Color
from tesserax.core import Bounds, Point, Shape

from .nodebox import RenderContext
from .nodes import Node
from .text import TextBlock


def centered(shape: Shape) -> Shape:
    """Move an unparented shape so its centre sits on the origin."""
    return shape.move_to(Point(0, 0), "center")


def at(shape: Shape, x: float, y: float) -> Shape:
    """Move an unparented shape so its centre sits at (x, y)."""
    return shape.move_to(Point(x, y), "center")


def label_block(
    node: Node,
    ctx: RenderContext,
    max_width: float,
    role: str = "label",
    color: Color | None = None,
) -> TextBlock:
    theme = ctx.theme
    return TextBlock(
        node.label,
        max_width,
        size=theme.size(role),
        fill=color if color is not None else theme.color("ink"),
        family=theme.typography.family,
        weight=theme.weight(role),
        line_height=theme.typography.line_height,
    )


def natural_width(node: Node, ctx: RenderContext) -> float:
    """Width the node's text wants on a single line, before any wrapping.

    Comparing a *wrapped* block against an available width is meaningless —
    wrapping always makes it fit. Callers deciding whether text belongs inside
    a shape must compare against this.
    """
    from .typography import measure

    theme = ctx.theme
    widths = [
        measure(
            node.label,
            theme.size("label"),
            theme.typography.family,
            theme.weight("label"),
        )
    ]
    if node.sublabel:
        widths.append(
            measure(
                node.sublabel,
                theme.size("sublabel"),
                theme.typography.family,
                theme.weight("sublabel"),
            )
        )
    return max(widths)


def text_stack(node: Node, ctx: RenderContext, max_width: float) -> Group:
    """Label plus optional sublabel, centred on the origin."""
    from tesserax.layout import ColumnLayout

    theme = ctx.theme
    parts: list[Shape] = [label_block(node, ctx, max_width)]
    if node.sublabel:
        parts.append(
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
    stack = ColumnLayout(parts, align="middle", gap=theme.geometry.gap / 6)
    centered(stack)
    return stack


def bar(
    node: Node,
    ctx: RenderContext,
    width: float,
    height: float,
    fill: Color,
    stroke: Color,
) -> Group:
    """A fixed-size rounded rectangle with its text centred inside."""
    theme = ctx.theme
    box = Rect(
        width,
        height,
        fill=fill,
        stroke=stroke,
        width=theme.geometry.stroke,
    )
    content = text_stack(node, ctx, width - 2 * theme.geometry.pad)
    return Group([box, content])


def trapezoid(
    top_width: float,
    bottom_width: float,
    height: float,
    fill: Color,
    stroke: Color,
    stroke_width: float,
) -> Path:
    """A trapezoid centred on the origin, built from explicit path commands."""
    half_h = height / 2
    return (
        Path(fill=fill, stroke=stroke, width=stroke_width)
        .jump_to(-top_width / 2, -half_h)
        .line_to(top_width / 2, -half_h)
        .line_to(bottom_width / 2, half_h)
        .line_to(-bottom_width / 2, half_h)
        .close()
    )


def measured_height(shape: Shape) -> float:
    return shape.local().height


def union_width(shapes: list[Shape]) -> float:
    if not shapes:
        return 0.0
    return max(s.local().width for s in shapes)


def bounds_of(shapes: list[Shape]) -> Bounds:
    return Bounds.union(*[s.bounds() for s in shapes])
