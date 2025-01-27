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
        self._coordinator = coordinator
        self._handlers: Dict[str, Callable] = {}
        self._active_commands: Dict[int, str] = {}
        self._logger = get_logger("chronicler.commands.processor")
        self._logger.info("COMMAND - Initializing command processor")
        self._logger.debug("COMMAND - No handlers registered")
        
    @property
    def handlers(self) -> Dict[str, Callable]:
        """Get registered handlers."""
        return self._handlers.copy()
        
    def register_command(self, command: str, handler: Callable):
        """Register a command handler."""
        if not command.startswith("/"):
            raise ValueError("Command must start with '/'")
        if not callable(handler):
            raise ValueError("Handler must be a callable")
        if command in self._handlers:
            raise ValueError(f"Handler for command {command} already registered")
        self._handlers[command] = handler
        self._logger.debug(f"COMMAND - Registered handler for {command}")

    def get_active_command(self, chat_id: int) -> Optional[str]:
        """Get the active command for a chat."""
        return self._active_commands.get(chat_id)
        
    def complete(self, chat_id: int) -> None:
        """Complete and clear the active command for a chat.
        
        Args:
            chat_id: The chat ID to complete the command for.
        """
        if chat_id in self._active_commands:
            self._logger.debug(f"COMMAND - Completing command for chat {chat_id}")
            self._active_commands.pop(chat_id, None)
        
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame through the command processor."""
        chat_id = frame.metadata.get("chat_id")
        
        if isinstance(frame, CommandFrame):
            # Clear any existing command context when starting a new command
            if chat_id is not None:
                self.complete(chat_id)
                
            # Handle unknown commands
            if frame.command not in self._handlers:
                raise ValueError(f"No handler registered for command {frame.command}")
                
            # Set new command context
            if chat_id is not None:
                self._active_commands[chat_id] = frame.command
                
            try:
                # Execute command handler
                response = await self._handlers[frame.command](frame)
                return response
            except Exception as e:
                # Clear command context on error
                if chat_id is not None:
                    self.complete(chat_id)
                raise  # Re-raise the exception
                
        elif chat_id is not None and chat_id in self._active_commands:
            # Handle continuation of existing command
            active_command = self._active_commands[chat_id]
            try:
                response = await self._handlers[active_command](frame)
                return response
            except Exception as e:
                # Clear command context on error
                self.complete(chat_id)
                raise  # Re-raise the exception
                
        return None  # Return None for non-command frames with no active context 