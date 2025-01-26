"""Event abstractions for different transport implementations."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

from chronicler.logging import trace_operation
from telethon.events import NewMessage
from telegram import Update

@dataclass
class EventMetadata:
    """Normalized metadata from transport events.
    
    Note: This is a placeholder for future multi-platform support.
    Currently only the Telegram-specific fields are used.
    """
    # Currently used (Telegram)
    chat_id: int
    chat_title: Optional[str] = None
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    message_id: Optional[int] = None
    
    # Future platform support (not used yet)
    platform: str = "telegram"  # 'telegram', 'twitter', 'discord'
    timestamp: Optional[datetime] = None
    reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    channel_id: Optional[str] = None  # Discord channel, Twitter thread
    guild_id: Optional[str] = None    # Discord server
    is_private: bool = False
    is_group: bool = False

class EventBase(ABC):
    """Abstract base class for transport events."""
    
    @abstractmethod
    def get_text(self) -> str:
        """Get message text."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> EventMetadata:
        """Get normalized event metadata."""
        pass
    
    @abstractmethod
    def get_command(self) -> Optional[str]:
        """Get command if message is a command, otherwise None."""
        pass
    
    @abstractmethod
    def get_command_args(self) -> List[str]:
        """Get command arguments if message is a command."""
        pass


"""Telegram transport events."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from telethon.events import NewMessage
from telegram import Update

class Update:
    """Base class for updates from transport libraries."""
    
    def __init__(self, update_obj: Any):
        """Initialize with update object."""
        self._update = update_obj
    
    @property
    def message_text(self) -> Optional[str]:
        """Get message text."""
        return self._update.message.text if hasattr(self._update, "message") else None
        
    @property
    def chat_id(self) -> Optional[int]:
        """Get chat ID."""
        return self._update.chat_id if hasattr(self._update, "chat_id") else None
        
    @property
    def chat_title(self) -> Optional[str]:
        """Get chat title."""
        return self._update.chat.title if hasattr(self._update, "chat") else None
        
    @property
    def sender_id(self) -> Optional[int]:
        """Get sender ID."""
        return self._update.sender_id if hasattr(self._update, "sender_id") else None
        
    @property
    def sender_name(self) -> Optional[str]:
        """Get sender name."""
        if hasattr(self._update, "sender") and self._update.sender:
            return self._update.sender.username or self._update.sender.first_name
        return None
        
    @property
    def message_id(self) -> Optional[int]:
        """Get message ID."""
        return self._update.message.id if hasattr(self._update, "message") else None
        
    @property
    def thread_id(self) -> Optional[str]:
        """Get thread ID."""
        return None
        
    @property
    def timestamp(self) -> Optional[float]:
        """Get message timestamp."""
        if hasattr(self._update, "message") and hasattr(self._update.message, "date"):
            return self._update.message.date.timestamp()
        return None

    def get_text(self) -> Optional[str]:
        """Get message text."""
        return self.message_text

    def get_metadata(self) -> EventMetadata:
        """Get event metadata."""
        return EventMetadata(
            chat_id=self.chat_id,
            chat_title=self.chat_title,
            sender_id=self.sender_id,
            sender_name=self.sender_name,
            message_id=self.message_id,
            platform="telegram",
            timestamp=self.timestamp,
            thread_id=self.thread_id
        )

    def get_command(self) -> Optional[str]:
        """Get command from text if present."""
        text = self.get_text()
        if text and text.startswith("/"):
            return text.split()[0]
        return None

    def get_command_args(self) -> List[str]:
        """Get command arguments if present."""
        text = self.get_text()
        if text and text.startswith("/"):
            return text.split()[1:]
        return []

class EventBase:
    """Base class for transport events."""

    def get_text(self) -> Optional[str]:
        """Get message text."""
        raise NotImplementedError

    def get_metadata(self) -> EventMetadata:
        """Get event metadata."""
        raise NotImplementedError

    def get_command_args(self) -> list[str]:
        """Get command arguments."""
        raise NotImplementedError

