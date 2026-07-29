"""Schema for the `hierarchy` archetype."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from ...nodes import Node


class TreeNode(Node):
    children: list[TreeNode] = []


TreeNode.model_rebuild()


class HierarchySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["down", "right"] = "down"
    root: TreeNode
