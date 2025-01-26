"""Command frame definitions."""
from typing import List
from dataclasses import dataclass, field
from chronicler.logging import get_logger

from .base import Frame

logger = get_logger(__name__)

@dataclass
class CommandFrame(Frame):
    """Frame for command messages."""
    command: str
    args: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate command frame data."""
        # Validate command
        if self.command is None:
            raise TypeError("command must be a string")
        if not isinstance(self.command, str):
            raise TypeError("command must be a string")
        if not self.command.startswith('/'):
            raise ValueError("Command must start with '/'")
            
        # Store original command for logging
        original_command = self.command
        # Normalize to lowercase but preserve slash
        self.command = self.command.lower()
        
        # Validate args
        if self.args is None:
            raise ValueError("Args must not be None")
        
        # Ensure all args are strings
        if not all(isinstance(arg, str) for arg in self.args):
            raise TypeError("All command arguments must be strings")
        
        logger.debug(f"FRAME - Created CommandFrame: /{self.command} (from {original_command}) with {len(self.args)} args")
        super().__post_init__() 