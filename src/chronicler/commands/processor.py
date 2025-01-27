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
from chronicler.storage.coordinator import StorageCoordinator

logger = get_logger(__name__)

class CommandProcessor(BaseProcessor):
    """Processor for command frames."""
    
    def __init__(self, coordinator: StorageCoordinator):
        """Initialize command processor.
        
        Args:
            coordinator: Storage coordinator.
        """
        super().__init__()
        self.coordinator = coordinator
        self._handlers: Dict[str, Callable[[Frame], Awaitable[Optional[Frame]]]] = {}
        self._active_commands: Dict[int, str] = {}  # chat_id -> active command
        self._logger = logger
        logger.info("COMMAND - Initializing command processor")
        logger.debug("COMMAND - No handlers registered")
        
    @property
    def handlers(self) -> Dict[str, Callable[[Frame], Awaitable[Optional[Frame]]]]:
        """Get registered handlers."""
        return self._handlers.copy()
        
    def register_command(self, command: str, handler: Callable[[Frame], Awaitable[Optional[Frame]]]) -> None:
        """Register a command handler.
        
        Args:
            command: Command to register.
            handler: Handler function.
            
        Raises:
            ValueError: If command is invalid or already registered.
        """
        if not command.startswith("/"):
            raise ValueError("Command must start with '/'")
        if command in self._handlers:
            raise ValueError(f"Handler for command {command} already registered")
        if not callable(handler):
            raise ValueError("Handler must be a callable")
            
        self._handlers[command] = handler
        logger.debug(f"COMMAND - Registered handler for {command}")
            
    def get_active_command(self, chat_id: int) -> Optional[str]:
        """Get active command for a chat.
        
        Args:
            chat_id: Chat ID.
            
        Returns:
            Active command or None if no command is active.
        """
        return self._active_commands.get(chat_id)
        
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a command frame."""
        if not isinstance(frame, CommandFrame):
            # If there's an active command, treat text frames as input
            chat_id = frame.metadata.get("chat_id")
            if chat_id and chat_id in self._active_commands:
                command = self._active_commands[chat_id]
                handler = self._handlers.get(command)
                if handler:
                    try:
                        response = await handler(frame)
                        if response and not response.content.startswith("Please provide"):
                            self._active_commands.pop(chat_id)
                        return response
                    except Exception as e:
                        self._logger.error(f"COMMAND - Handler error for command {command}: {str(e)}")
                        raise
            return None

        command = frame.command
        handler = self._handlers.get(command)
        if not handler:
            self._logger.error(f"COMMAND - No handler registered for command {command}")
            raise ValueError(f"No handler registered for command {command}")

        chat_id = frame.metadata.get("chat_id")
        if chat_id:
            self._active_commands[chat_id] = command

        try:
            response = await handler(frame)
            if response and not response.content.startswith("Please provide"):
                self._active_commands.pop(chat_id, None)
            return response
        except Exception as e:
            self._logger.error(f"COMMAND - Handler error for command {command}: {str(e)}")
            raise 