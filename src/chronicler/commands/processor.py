"""Command processor for handling command frames."""
from typing import Dict, Optional, Callable, Awaitable

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame
from chronicler.frames.command import CommandFrame
from chronicler.exceptions import (
    CommandError,
    CommandValidationError,
    CommandStorageError,
    CommandAuthorizationError
)
from chronicler.logging import get_logger
from chronicler.processors.base import BaseProcessor

logger = get_logger(__name__)

class CommandProcessor(BaseProcessor):
    """Processor for command frames."""
    
    def __init__(self, coordinator=None):
        """Initialize command processor.
        
        Args:
            coordinator: Optional storage coordinator instance.
        """
        super().__init__()
        self._handlers: Dict[str, Callable[[Frame], Awaitable[Optional[Frame]]]] = {}
        self.coordinator = coordinator
        logger.info("COMMAND - Initializing command processor")
        logger.debug("COMMAND - No handlers registered")
        
    @property
    def handlers(self) -> Dict[str, Callable[[Frame], Awaitable[Optional[Frame]]]]:
        """Get registered handlers."""
        return self._handlers.copy()
        
    def register_command(self, command: str, handler: Callable[[Frame], Awaitable[Optional[Frame]]]) -> None:
        """Register a command handler function.
        
        Args:
            command: The command to handle (e.g. "start" for /start)
            handler: Async function that takes a Frame and returns an Optional[Frame]
            
        Raises:
            ValueError: If command format is invalid or handler is not callable
        """
        if not callable(handler):
            raise ValueError("Handler must be a callable")
            
        # Validate command format
        if not command.startswith('/'):
            raise ValueError("Command must start with '/'")
            
        if command in self._handlers:
            raise ValueError(f"Handler for command {command} already registered")
            
        self._handlers[command] = handler
        logger.debug(f"COMMAND - Registered handler for {command}")
            
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame.
        
        Args:
            frame: The frame to process.
            
        Returns:
            The processed frame or None if the frame was handled or is not a command.
            
        Raises:
            ValueError: If no handler is registered for a command.
        """
        if not isinstance(frame, CommandFrame):
            return None  # Pass through non-command frames

        command = frame.command
        if command not in self._handlers:
            logger.error(f"COMMAND - No handler registered for command {command}")
            raise ValueError(f"No handler registered for command {command}")

        try:
            handler = self._handlers[command]
            result = await handler(frame)
            logger.info(f"COMMAND - Successfully handled command: {command}")
            return result
        except Exception as e:
            logger.error(f"COMMAND - Error handling command {command}: {e}")
            raise  # Re-raise the original exception 