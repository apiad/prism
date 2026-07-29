from ...registry import register
from .build import MatrixArchetype
from .schema import MatrixSpec

register(MatrixArchetype())

__all__ = ["MatrixArchetype", "MatrixSpec"]
