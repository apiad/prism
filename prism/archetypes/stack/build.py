"""Tiers drawn as full-width bars, read top-down or bottom-up."""

from __future__ import annotations

from tesserax import Group
from tesserax.layout import ColumnLayout

from ...nodebox import RenderContext
from ...shapes import bar, text_stack
from ...text import MeasuredText
from .schema import StackSpec

MIN_WIDTH = 220.0


class StackArchetype:
    name = "stack"
    spec_model = StackSpec
    supports_note = False

    def build(self, spec: StackSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        layers = list(spec.layers)
        if spec.order == "bottom_up":
            layers = list(reversed(layers))

        # Size every bar to the widest content so the stack reads as one block.
        probes = [text_stack(layer, ctx, 320) for layer in layers]
        width = max(MIN_WIDTH, max(p.local().width for p in probes)) + (
            4 * theme.geometry.pad
        )
        height = max(p.local().height for p in probes) + 2 * theme.geometry.pad

        bars: list[Group] = []
        for index, layer in enumerate(layers):
            accent = layer.accent if layer.accent is not None else index
            bars.append(
                bar(
                    layer,
                    ctx,
                    width,
                    height,
                    fill=theme.color("surface"),
                    stroke=theme.color(accent),
                )
            )

        column = ColumnLayout(bars, align="middle", gap=theme.geometry.stroke * 3)

        annotations: list[Group] = []
        for layer, drawn in zip(layers, bars, strict=True):
            if not layer.side:
                continue
            tag = MeasuredText(
                layer.side,
                size=theme.size("note"),
                fill=theme.color("muted"),
                family=theme.typography.family,
                weight=theme.weight("note"),
                anchor="start",
            )
            edge = drawn.bounds().right
            tag.move_to(edge.dx(theme.geometry.pad), "left")
            annotations.append(tag)

        return Group([column, *annotations])
