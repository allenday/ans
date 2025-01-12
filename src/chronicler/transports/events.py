"""Event abstractions for different transport implementations."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class EventMetadata:
    """Normalized metadata from transport events.
    
    Note: This is a placeholder for future multi-platform support.
    Currently only the Telegram-specific fields are used.
    """
    # Currently used (Telegram)
    chat_id: int
    chat_title: Optional[str]
    sender_id: Optional[int]
    sender_name: Optional[str]
    message_id: int
    
    # Future platform support (not used yet)
    platform: str = "telegram"  # 'telegram', 'twitter', 'discord'
    timestamp: Optional[datetime] = None
    reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    channel_id: Optional[str] = None  # Discord channel, Twitter thread
    guild_id: Optional[str] = None    # Discord server
    is_private: bool = False
    is_group: bool = False
    
    def get(self, field: str, default=None):
        """Get a field value with an optional default."""
        return getattr(self, field, default)

class EventBase(ABC):
    """Abstract base class for transport events."""
    
    @abstractmethod
    async def get_text(self) -> str:
        """Get message text."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> EventMetadata:
        """Get normalized event metadata."""
        pass
    
    @abstractmethod
    async def get_command(self) -> Optional[str]:
        """Get command if message is a command, otherwise None."""
        pass
    
    @abstractmethod
    async def get_command_args(self) -> List[str]:
        """Get command arguments if message is a command."""
        pass

class TelethonEvent(EventBase):
    """Wrapper for Telethon events."""
    
    def __init__(self, event):
        self._event = event
    
    async def get_text(self) -> str:
        return self._event.message.text
    
    def get_metadata(self) -> EventMetadata:
        # Handle sender info safely
        sender_id = self._event.sender_id if self._event.sender_id else None
        sender_name = None
        if self._event.sender:
            sender_name = self._event.sender.username or self._event.sender.first_name
        
        return EventMetadata(
            chat_id=self._event.chat_id,
            chat_title=self._event.chat.title if hasattr(self._event.chat, 'title') else None,
            sender_id=sender_id,
            sender_name=sender_name,
            message_id=self._event.message.id
        )
    
    async def get_command(self) -> Optional[str]:
        """Get command from event if present."""
        text = await self.get_text()
        if isinstance(text, str) and text.startswith('/'):
            return text.split()[0].lower()
        return None
    
    async def get_command_args(self) -> List[str]:
        """Get command arguments from event."""
        text = await self.get_text()
        if isinstance(text, str) and text.startswith('/'):
            parts = text.split()
            return parts[1:] if len(parts) > 1 else []
        return []
    
    async def get_chat_id(self) -> int:
        """Get chat ID."""
        return self._event.chat_id
    
    async def get_chat_title(self) -> str:
        """Get chat title."""
        return self._event.chat.title

    async def get_sender_id(self) -> int:
        """Get sender ID."""
        return self._event.sender_id

    async def get_sender_username(self) -> str:
        """Get sender username."""
        return self._event.sender.username

    async def get_sender_name(self) -> str:
        """Get sender name."""
        return self._event.sender.first_name

class TelegramBotEvent(EventBase):
    """Wrapper for python-telegram-bot events."""
    
    def __init__(self, update, context):
        self._update = update
        self._context = context
    
    async def get_text(self) -> str:
        return self._update.effective_message.text
    
    def get_metadata(self) -> EventMetadata:
        return EventMetadata(
            chat_id=self._update.effective_chat.id,
            chat_title=self._update.effective_chat.title,
            sender_id=self._update.effective_user.id if self._update.effective_user else None,
            sender_name=(self._update.effective_user.username or self._update.effective_user.first_name) 
                if self._update.effective_user else None,
            message_id=self._update.effective_message.message_id
        )
    
    async def get_command(self) -> Optional[str]:
        """Get command from event if present."""
        text = await self.get_text()
        if isinstance(text, str) and text.startswith('/'):
            return text.split()[0].lower()
        return None
    
    async def get_command_args(self) -> List[str]:
        if self._context and self._context.args:
            return self._context.args
        text = await self.get_text()
        parts = text.split()
        return parts[1:] if len(parts) > 1 else [] 
    
    async def get_chat_id(self) -> int:
        """Get chat ID."""
        return self._update.effective_chat.id
    
    async def get_chat_title(self) -> str:
        """Get chat title."""
        return self._update.effective_chat.title

    async def get_sender_id(self) -> int:
        """Get sender ID."""
        return self._update.effective_user.id

    async def get_sender_username(self) -> str:
        """Get sender username."""
        return self._update.effective_user.username

    async def get_sender_name(self) -> str:
        """Get sender name."""
        return self._update.effective_user.first_name 