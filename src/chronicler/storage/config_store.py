from dataclasses import dataclass
from typing import Dict, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScribeState:
    """Persistent scribe state"""
    user_sessions: Dict[int, dict]  # user_id -> session data
    group_configs: Dict[int, dict]  # group_id -> config data
    
class ConfigStore:
    """Simple JSON-based config storage"""
    def __init__(self, config_path: str = "scribe_state.json"):
        self.config_path = config_path
        logger.debug(f"Initialized ConfigStore with path: {config_path}")
        
    async def load_state(self) -> ScribeState:
        """Load scribe state from disk"""
        logger.info(f"Loading scribe state from {self.config_path}")
        if not os.path.exists(self.config_path):
            logger.debug(f"Config file not found at {self.config_path}, returning empty state")
            return ScribeState({}, {})
            
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                state = ScribeState(
                    user_sessions=data.get('user_sessions', {}),
                    group_configs=data.get('group_configs', {})
                )
                logger.debug(f"Loaded state with {len(state.user_sessions)} sessions and {len(state.group_configs)} group configs")
                return state
        except Exception as e:
            logger.error(f"Failed to load scribe state: {e}", exc_info=True)
            return ScribeState({}, {})
    
    async def save_state(self, state: ScribeState) -> None:
        """Save scribe state to disk"""
        logger.info(f"Saving scribe state to {self.config_path}")
        try:
            with open(self.config_path, 'w') as f:
                data = {
                    'user_sessions': state.user_sessions,
                    'group_configs': state.group_configs
                }
                json.dump(data, f, indent=2)
                logger.debug(f"Successfully saved state with {len(state.user_sessions)} sessions and {len(state.group_configs)} group configs")
        except Exception as e:
            logger.error(f"Failed to save scribe state: {e}", exc_info=True) 