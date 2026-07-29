from ...registry import register
from .build import ComparisonArchetype
from .schema import ComparisonSpec

register(ComparisonArchetype())

__all__ = ["ComparisonArchetype", "ComparisonSpec"]
