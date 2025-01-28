"""Command parser implementation."""
from typing import List, Optional, Tuple
from chronicler.frames.command import CommandFrame
from chronicler.frames.base import Frame
from chronicler.logging import get_logger

logger = get_logger(__name__)

class CommandParser:
    """Parser for command frames."""

    @staticmethod
    def parse_command(text: str) -> Tuple[str, List[str]]:
        """Parse a command string into command and arguments.
        
        Args:
            text: The command string to parse
            
        Returns:
            Tuple[str, List[str]]: The command and list of arguments
            
        Example:
            >>> CommandParser.parse_command("/config repo token")
            ("/config", ["repo", "token"])
        """
        parts = text.strip().split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        return command, args

    @staticmethod
    def is_command(text: str) -> bool:
        """Check if text is a command.
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if text starts with '/', False otherwise
        """
        return text.strip().startswith('/') 