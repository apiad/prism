"""Schema for the `hierarchy` archetype."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...nodes import Node


class TreeNode(Node):
    # default_factory, not [] — pydantic copies per instance either way,
    # but the literal trips RUF012 and reads as shared state.
    children: list[TreeNode] = Field(default_factory=list)


TreeNode.model_rebuild()


class HierarchySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["down", "right"] = "down"
    root: TreeNode
