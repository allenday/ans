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

logger = get_logger(__name__)

class CommandProcessor:
    """Processor for command frames."""
    
    def __init__(self, coordinator=None):
        """Initialize command processor.
        
        Args:
            coordinator: Optional storage coordinator instance.
        """
        self._handlers: Dict[str, CommandHandler] = {}
        self.coordinator = coordinator
        logger.info("COMMAND - Initializing command processor")
        logger.debug("COMMAND - No handlers registered")
        
    @property
    def handlers(self) -> Dict[str, CommandHandler]:
        """Get registered handlers."""
        return self._handlers.copy()
        
    def register_handler(self, handler: CommandHandler, command: Optional[str] = None) -> None:
        """Register a command handler.
        
        Args:
            handler: The command handler to register.
            command: Optional command to register the handler for. If not provided,
                    will use handler.command.
            
        Raises:
            ValueError: If handler is not a CommandHandler instance or command is invalid.
        """
        if handler is None:
            raise ValueError("Handler cannot be None")
            
        if not isinstance(handler, CommandHandler):
            raise ValueError("Handler must be an instance of CommandHandler")
            
        # Use provided command or get from handler
        cmd = command if command is not None else handler.command
        if not cmd:
            raise ValueError("Handler must have a command")
            
        if not isinstance(cmd, str):
            raise ValueError("Command must be a string")
            
        if not cmd.startswith('/'):
            raise ValueError("Command must start with '/'")
            
        cmd = cmd.lower()
        if cmd in self._handlers:
            raise ValueError(f"Handler for command {cmd} already registered")
            
        self._handlers[cmd] = handler
        logger.info(f"COMMAND - Registered handler for {cmd}")
        
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a command frame.
        
        Args:
            frame: The frame to process.
            
        Returns:
            Optional[Frame]: The response frame, if any.
            
        Raises:
            CommandError: If command processing fails.
            ValueError: If no handler is registered for the command.
            Any exception raised by the handler.
        """
        # Check if frame is a CommandFrame by checking its class name
        # This avoids issues with module imports
        if frame.__class__.__name__ != "CommandFrame":
            logger.debug(f"COMMAND - Ignoring non-command frame: {type(frame)}")
            return None
            
        command = frame.command.lower()
        handler = self._handlers.get(command)
        
        if not handler:
            logger.warning(f"COMMAND - No handler registered for {command}")
            raise ValueError(f"No handler registered for command {command}")
            
        try:
            logger.debug(f"COMMAND - Processing {command} with {handler.__class__.__name__}")
            result = await handler.handle(frame)
            
            if result is None:
                result = TextFrame(
                    content=f"Command {command} executed successfully",
                    metadata=frame.metadata
                )
                
            return result
            
        except (CommandValidationError, CommandStorageError, CommandAuthorizationError) as e:
            logger.error(f"COMMAND - Error processing {command}: {str(e)}")
            return TextFrame(
                content=str(e),
                metadata=frame.metadata
            )
            
        except Exception as e:
            logger.error(f"COMMAND - Error processing {command}: {str(e)}")
            raise 