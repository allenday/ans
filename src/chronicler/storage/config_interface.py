from dataclasses import dataclass
from typing import Dict, Protocol, Any

@dataclass
class BotState:
    """Persistent bot state"""
    user_sessions: Dict[int, dict]  # user_id -> session data
    group_configs: Dict[int, dict]  # group_id -> config data
    config: Dict[str, Any]  # bot configuration

class ConfigStorageAdapter(Protocol):
    """Interface for bot configuration storage"""
    
    async def load(self) -> Dict[str, Any]:
        """Load bot state"""
        ...
    
    async def save(self, state: Dict[str, Any]) -> None:
        """Save bot state"""
        ... 