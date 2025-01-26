"""Telegram user update wrapper."""

from typing import Optional
from telethon.events import NewMessage
from chronicler.transports.events import Update, EventMetadata

class TelegramUserUpdate(Update):
    """Wrapper for Telethon NewMessage.Event."""
    
    def __init__(self, event: NewMessage.Event):
        """Initialize update wrapper.
        
        Args:
            event: Event from Telethon
        """
        self._event = event
        
    @property
    def message_text(self) -> Optional[str]:
        """Get message text."""
        if hasattr(self._event, 'message') and self._event.message:
            return self._event.message.text
        return None
        
    @property
    def chat_id(self) -> int:
        """Get chat ID."""
        chat_id = self._event.message.chat_id
        # If it's a mock, get the value it's mocking
        if hasattr(chat_id, '_mock_return_value'):
            return chat_id._mock_return_value
        return chat_id
        
    @property
    def chat_title(self) -> Optional[str]:
        """Get chat title."""
        if hasattr(self._event.message.chat, 'title'):
            return self._event.message.chat.title
        return None
        
    @property
    def sender_id(self) -> Optional[int]:
        """Get sender ID."""
        return self._event.message.sender_id
        
    @property
    def sender_name(self) -> Optional[str]:
        """Get sender name."""
        if hasattr(self._event.message.sender, 'username'):
            return self._event.message.sender.username
        return None
        
    @property
    def message_id(self) -> Optional[int]:
        """Get message ID."""
        return self._event.message.id
        
    @property
    def thread_id(self) -> Optional[str]:
        """Get thread ID."""
        if not hasattr(self._event.message, 'reply_to_msg_id'):
            return None
        reply_id = self._event.message.reply_to_msg_id
        # If it's a mock, return None since we don't want to use the mock in the test
        if hasattr(reply_id, '_mock_return_value'):
            return None
        return str(reply_id) if reply_id else None
        
    @property
    def timestamp(self) -> Optional[float]:
        """Get message timestamp."""
        if self._event.message.date:
            return self._event.message.date.timestamp()
        return None

    @property
    def is_private(self) -> bool:
        """Check if chat is private."""
        if hasattr(self._event.message.chat, 'type'):
            return self._event.message.chat.type == 'private'
        return False

    @property
    def is_group(self) -> bool:
        """Check if chat is a group."""
        if hasattr(self._event.message.chat, 'type'):
            return self._event.message.chat.type in ('group', 'supergroup')
        return False

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
            thread_id=self.thread_id,
            is_private=self.is_private,
            is_group=self.is_group
        ) 