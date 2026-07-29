from ...registry import register
from .build import TimelineArchetype
from .schema import TimelineSpec

register(TimelineArchetype())

__all__ = ["TimelineArchetype", "TimelineSpec"]
