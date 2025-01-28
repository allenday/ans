"""Telegram bot update implementation."""
from typing import Optional, List
from telegram import Update

from chronicler.metadata import EventMetadata

class TelegramBotUpdate:
    """Update implementation for Telegram bot API."""

    def __init__(self, update: Update):
        """Initialize with update object."""
        self._update = update

    @property
    def message_text(self) -> Optional[str]:
        """Get message text."""
        return self._update.message.text if hasattr(self._update, "message") else None

    @property
    def chat_id(self) -> Optional[int]:
        """Get chat ID."""
        return self._update.message.chat.id if hasattr(self._update, "message") else None

    @property
    def chat_title(self) -> Optional[str]:
        """Get chat title."""
        return self._update.message.chat.title if hasattr(self._update, "message") else None

    @property
    def sender_id(self) -> Optional[int]:
        """Get sender ID."""
        return self._update.message.from_user.id if hasattr(self._update, "message") else None

    @property
    def sender_name(self) -> Optional[str]:
        """Get sender name."""
        if hasattr(self._update, "message") and self._update.message.from_user:
            return self._update.message.from_user.username or self._update.message.from_user.first_name
        return None

    @property
    def message_id(self) -> Optional[int]:
        """Get message ID."""
        return self._update.message.message_id if hasattr(self._update, "message") else None

    @property
    def thread_id(self) -> Optional[str]:
        """Get thread ID."""
        return str(self._update.message.message_thread_id) if hasattr(self._update, "message") else None

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