"""Wrap an archetype's body with title, caption and accessibility metadata."""

from __future__ import annotations

from xml.sax.saxutils import escape

from tesserax import Canvas, Group
from tesserax.layout import ColumnLayout

from .envelope import Envelope
from .nodebox import RenderContext
from .text import TextBlock


def frame(body: Group, envelope: Envelope, ctx: RenderContext) -> Canvas:
    theme = ctx.theme
    parts: list = []

    if envelope.title:
        parts.append(
            TextBlock(
                envelope.title,
                envelope.width,
                size=theme.size("title"),
                fill=theme.color("ink"),
                family=theme.typography.family,
                weight=theme.weight("title"),
                line_height=theme.typography.line_height,
            )
        )
    if envelope.subtitle:
        parts.append(
            TextBlock(
                envelope.subtitle,
                envelope.width,
                size=theme.size("subtitle"),
                fill=theme.color("muted"),
                family=theme.typography.family,
                weight=theme.weight("subtitle"),
                line_height=theme.typography.line_height,
            )
        )

    parts.append(body)

    if envelope.caption:
        parts.append(
            TextBlock(
                envelope.caption,
                envelope.width,
                size=theme.size("note"),
                fill=theme.color("muted"),
                family=theme.typography.family,
                weight=theme.weight("note"),
                line_height=theme.typography.line_height,
            )
        )

    stacked = ColumnLayout(parts, align="middle", gap=theme.geometry.gap)

    canvas = Canvas(width=envelope.width, height=envelope.width)
    canvas.add(stacked, mode="loose")
    canvas.fit(padding=theme.geometry.gap)
    return canvas


def with_accessibility(svg: str, envelope: Envelope) -> str:
    """Inject role, <title> and <desc> into a rendered SVG."""
    title = escape(envelope.title or f"{envelope.type} diagram")
    desc = escape(envelope.caption or envelope.subtitle or title)
    head, rest = svg.split(">", 1)
    return f'{head} role="img">\n<title>{title}</title>\n<desc>{desc}</desc>{rest}'
