from ...registry import register
from .build import HubArchetype
from .schema import HubSpec

register(HubArchetype())

__all__ = ["HubArchetype", "HubSpec"]
