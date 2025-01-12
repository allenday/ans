"""Command frame definitions."""
import logging
from typing import List
from dataclasses import dataclass, field

from .base import Frame

logger = logging.getLogger(__name__)

@dataclass
class CommandFrame(Frame):
    """Frame for command messages."""
    command: str
    args: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate command frame data."""
        # Validate command
        if not self.command.startswith('/'):
            raise ValueError("Command must start with '/'")
        self.command = self.command.lower()  # Normalize to lowercase
        
        # Validate args
        if self.args is None:
            raise ValueError("Args must not be None")
        
        # Ensure all args are strings
        if not all(isinstance(arg, str) for arg in self.args):
            raise TypeError("All command arguments must be strings")
        
        logger.debug(f"FRAME - Created CommandFrame: {self.command} with {len(self.args)} args")
        super().__post_init__() 