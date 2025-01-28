"""Abstract command base class."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.logging import get_logger

logger = get_logger(__name__)

class Command(ABC):
    """Abstract base class for all commands."""

    def __init__(self):
        """Initialize command."""
        self.logger = get_logger(__name__)
        self.logger.debug("COMMAND - Initialized Command")

    @abstractmethod
    async def execute(self, frame: Frame) -> Optional[Frame]:
        """Execute the command.
        
        Args:
            frame: The frame to process
            
        Returns:
            Optional[Frame]: The processed frame, or None if no response
        """
        pass 