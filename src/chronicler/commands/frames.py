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
        
        # Validate command
        if not isinstance(self.command, str):
            raise TypeError("command must be a string")
            
        if not self.command:
            raise ValueError("Command cannot be empty")
            
        if not self.command.startswith('/'):
            raise ValueError("Command must start with '/'")
            
        # Normalize command to lowercase
        self.command = self.command.lower()
        
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