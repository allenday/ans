from dataclasses import dataclass
from typing import Dict, Protocol, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScribeState:
    """Persistent scribe state"""
    user_sessions: Dict[int, dict]  # user_id -> session data
    group_configs: Dict[int, dict]  # group_id -> config data
    config: Dict[str, Any]  # scribe configuration
    
    def __post_init__(self):
        logger.debug("Creating scribe state")
        logger.debug(f"User sessions: {len(self.user_sessions)}")
        logger.debug(f"Group configs: {len(self.group_configs)}")
        logger.debug(f"Config keys: {list(self.config.keys()) if self.config else []}")

class ConfigStorageAdapter(Protocol):
    """Interface for scribe configuration storage"""
    
    async def load_state(self) -> Dict[str, Any]:
        """Load scribe state"""
        ...
    
    async def save_state(self, state: Dict[str, Any]) -> None:
        """Save scribe state"""
        ... 