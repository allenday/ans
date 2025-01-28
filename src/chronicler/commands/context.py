"""Command context implementation."""
from typing import Optional, Dict, Any
from chronicler.logging import get_logger

logger = get_logger(__name__)

class CommandContext:
    """Context for command execution."""

    def __init__(self):
        """Initialize command context."""
        self.active_commands: Dict[int, str] = {}
        self.logger = get_logger(__name__)
        self.logger.debug("CONTEXT - Initialized command context")

    def get_active_command(self, chat_id: int) -> Optional[str]:
        """Get the active command for a chat.
        
        Args:
            chat_id: The chat ID to get the active command for
            
        Returns:
            Optional[str]: The active command, or None if no active command
        """
        return self.active_commands.get(chat_id)

    def set_active_command(self, chat_id: int, command: str) -> None:
        """Set the active command for a chat.
        
        Args:
            chat_id: The chat ID to set the active command for
            command: The command to set as active
        """
        self.active_commands[chat_id] = command
        self.logger.debug(f"CONTEXT - Set active command {command} for chat {chat_id}")

    def complete_command(self, chat_id: int) -> None:
        """Complete and clear the active command for a chat.
        
        Args:
            chat_id: The chat ID to complete the command for
        """
        if chat_id in self.active_commands:
            self.logger.debug(f"CONTEXT - Completing command for chat {chat_id}")
            self.active_commands.pop(chat_id, None) 