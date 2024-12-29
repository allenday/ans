from dataclasses import dataclass
from typing import Dict, Optional
import json
import os

@dataclass
class BotState:
    """Persistent bot state"""
    user_sessions: Dict[int, dict]  # user_id -> session data
    group_configs: Dict[int, dict]  # group_id -> config data
    
class ConfigStore:
    """Simple JSON-based config storage"""
    def __init__(self, config_path: str = "bot_state.json"):
        self.config_path = config_path
        
    async def load_state(self) -> BotState:
        """Load bot state from disk"""
        if not os.path.exists(self.config_path):
            return BotState({}, {})
            
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            return BotState(
                user_sessions=data.get('user_sessions', {}),
                group_configs=data.get('group_configs', {})
            )
    
    async def save_state(self, state: BotState) -> None:
        """Save bot state to disk"""
        with open(self.config_path, 'w') as f:
            json.dump({
                'user_sessions': state.user_sessions,
                'group_configs': state.group_configs
            }, f, indent=2) 