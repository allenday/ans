"""Telegram user update implementation."""
from typing import Optional, List
from telethon.events import NewMessage

from chronicler.metadata import EventMetadata

class TelegramUserUpdate:
    """Update implementation for Telegram user API."""

    def __init__(self, update: NewMessage.Event):
        """Initialize with update object."""
        self._update = update

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