from ...registry import register
from .build import StackArchetype
from .schema import StackSpec

register(StackArchetype())

__all__ = ["StackArchetype", "StackSpec"]
