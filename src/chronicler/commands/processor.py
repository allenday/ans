"""Command processor for handling command frames."""
from typing import Dict, Optional, Type

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame
from chronicler.frames.command import CommandFrame
from chronicler.handlers.command import CommandHandler
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
        self._handlers: Dict[str, CommandHandler] = {}
        self.coordinator = coordinator
        logger.info("COMMAND - Initializing command processor")
        logger.debug("COMMAND - No handlers registered")
        
    @property
    def handlers(self) -> Dict[str, CommandHandler]:
        """Get registered handlers."""
        return self._handlers.copy()
        
    def register_handler(self, handler: CommandHandler, command: str = None) -> None:
        """Register a command handler.
        
        Args:
            handler: The command handler to register.
            command: Optional command to handle. If not provided, will use handler.command.
            
        Raises:
            ValueError: If handler is not a CommandHandler instance or command is invalid.
        """
        if handler is None:
            raise ValueError("Handler cannot be None")
            
        if not isinstance(handler, CommandHandler):
            raise ValueError(f"Handler must be an instance of CommandHandler (got {type(handler)})")
            
        # Get command from handler if not provided
        cmd = command if command is not None else getattr(handler, 'command', None)
        if not cmd:
            raise ValueError("Command must be provided either as argument or as handler.command attribute")
            
        if not isinstance(cmd, str) or not cmd.startswith('/'):
            raise ValueError("Invalid command format - must start with '/'")
            
        if cmd in self._handlers:
            raise ValueError(f"Handler for command {cmd} already registered")
            
        self._handlers[cmd] = handler
        logger.debug(f"COMMAND - Registered handler for {cmd}")
        
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
            result = await handler.handle(frame)
            logger.info(f"COMMAND - Successfully handled command: {command}")
            return result
        except Exception as e:
            logger.error(f"COMMAND - Error handling command {command}: {e}")
            raise  # Re-raise the original exception 