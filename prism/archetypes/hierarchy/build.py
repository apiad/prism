"""A tree, laid out by tesserax's HierarchicalLayout.

Data recursion through `children` is allowed here: a tree is recursive by
nature. That is distinct from template composition, which prism does not do.
"""

from __future__ import annotations

from tesserax import Group
from tesserax.core import Shape
from tesserax.layout import HierarchicalLayout

from ...connectors import connect
from ...nodebox import RenderContext, build_node_box
from .schema import HierarchySpec, TreeNode


class HierarchyArchetype:
    name = "hierarchy"
    spec_model = HierarchySpec

    def build(self, spec: HierarchySpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        boxes: dict[int, Shape] = {}
        edges: list[tuple[Shape, Shape]] = []

        def walk(node: TreeNode) -> Shape:
            box = build_node_box(node, ctx, max_width=140)
            boxes[id(node)] = box
            for child in node.children:
                edges.append((box, walk(child)))
            return box

        walk(spec.root)

        orientation = "vertical" if spec.direction == "down" else "horizontal"
        layout = HierarchicalLayout(
            list(boxes.values()),
            rank_sep=theme.geometry.gap * 1.6,
            node_sep=theme.geometry.gap,
            orientation=orientation,
        )
        for parent, child in edges:
            layout.connect(parent, child)
        # Connections are declared after construction, so rank the tree again.
        layout.do_layout()

        tail, head = (
            ("bottom", "top") if spec.direction == "down" else ("right", "left")
        )
        connectors = [connect(p, c, tail, head, theme) for p, c in edges]

        return Group([layout, *connectors])
