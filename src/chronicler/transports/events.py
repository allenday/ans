"""Event abstractions for different transport implementations."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from chronicler.logging import trace_operation

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

class TelethonEvent(EventBase):
    """Wrapper for Telethon events."""
    
    def __init__(self, event):
        self._event = event
    
    @trace_operation('transport.events.telethon')
    def get_text(self) -> str:
        return self._event.message.text
    
    @trace_operation('transport.events.telethon')
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
    
    @trace_operation('transport.events.telethon')
    def get_command(self) -> Optional[str]:
        text = self.get_text()
        if text.startswith('/'):
            return text.split()[0].lower()
        return None
    
    @trace_operation('transport.events.telethon')
    def get_command_args(self) -> List[str]:
        text = self.get_text()
        parts = text.split()
        return parts[1:] if len(parts) > 1 else []

class TelegramBotEvent(EventBase):
    """Wrapper for python-telegram-bot events."""
    
    def __init__(self, update, context):
        self._update = update
        self._context = context
    
    @trace_operation('transport.events.telegram_bot')
    def get_text(self) -> str:
        return self._update.message.text
    
    @trace_operation('transport.events.telegram_bot')
    def get_metadata(self) -> EventMetadata:
        return EventMetadata(
            chat_id=self._update.message.chat_id,
            chat_title=self._update.message.chat.title,
            sender_id=self._update.message.from_user.id if self._update.message.from_user else None,
            sender_name=(self._update.message.from_user.username or self._update.message.from_user.first_name) 
                if self._update.message.from_user else None,
            message_id=self._update.message.message_id
        )
    
    @trace_operation('transport.events.telegram_bot')
    def get_command(self) -> Optional[str]:
        text = self.get_text()
        if text.startswith('/'):
            return text.split()[0].lower()
        return None
    
    @trace_operation('transport.events.telegram_bot')
    def get_command_args(self) -> List[str]:
        if self._context and self._context.args:
            return self._context.args
        text = self.get_text()
        parts = text.split()
        return parts[1:] if len(parts) > 1 else [] 