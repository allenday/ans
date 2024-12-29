import json
from pathlib import Path
from typing import Dict, Any
from chronicler.storage.config_interface import ConfigStorageAdapter

class JsonConfigStorage(ConfigStorageAdapter):
    """JSON file-based configuration storage"""
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            self.config_file.write_text("{}")

    async def load_state(self) -> Dict[str, Any]:
        """Load state from JSON file"""
        try:
            return json.loads(self.config_file.read_text())
        except json.JSONDecodeError:
            return {}

    async def save_state(self, state: Dict[str, Any]) -> None:
        """Save state to JSON file"""
        self.config_file.write_text(json.dumps(state, indent=2)) 