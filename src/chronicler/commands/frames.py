"""Command frames for the command processor."""
from dataclasses import dataclass, field
from typing import List, Optional

from chronicler.frames.base import Frame
from chronicler.exceptions import CommandValidationError
from chronicler.logging import get_logger

logger = get_logger(__name__)

@dataclass
class CommandFrame(Frame):
    """Frame for command messages."""
    
    command: str
    args: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate command frame attributes."""
        super().__post_init__()

        # Validate command type first
        if not isinstance(self.command, str):
            raise TypeError("command must be a string")
            
        # Parse command string if it contains spaces
        if ' ' in self.command:
            parts = self.command.strip().split()
            if not parts:
                raise ValueError("Command cannot be empty")
            
            # First part is the command
            self.command = parts[0].lower()
            
            # Rest are args if no args were provided
            if not self.args:
                self.args = parts[1:] if len(parts) > 1 else []
        else:
            # Just normalize the command
            self.command = self.command.strip().lower()
        
        if not self.command:
            raise ValueError("Command cannot be empty")
            
        if not self.command.startswith('/'):
            raise ValueError("Invalid command format - must start with '/'")
            
        # Initialize args if None
        if self.args is None:
            raise ValueError("Args must not be None")
            
        # Validate args
        if not isinstance(self.args, list):
            raise TypeError("Arguments must be a list")
            
        # Validate each argument is a string
        for i, arg in enumerate(self.args):
            if not isinstance(arg, str):
                raise TypeError("All command arguments must be strings")
        
        logger.debug(f"Created CommandFrame: {self.command} with {len(self.args)} args") 