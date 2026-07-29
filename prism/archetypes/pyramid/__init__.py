from ...registry import register
from .build import PyramidArchetype
from .schema import PyramidSpec

register(PyramidArchetype())

__all__ = ["PyramidArchetype", "PyramidSpec"]
