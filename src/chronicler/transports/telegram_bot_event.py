"""Telegram bot event implementation."""

from typing import Optional
from chronicler.transports.events import EventBase, EventMetadata
from chronicler.transports.telegram_bot_update import TelegramBotUpdate

class TelegramBotEvent(EventBase):
    """Event from Telegram bot API."""

    def __init__(self, update: TelegramBotUpdate, metadata: dict | EventMetadata = None):
        """Initialize event.
        
        Args:
            update: Update from Telegram bot API
            metadata: Event metadata as dict or EventMetadata object
        """
        self.update = update
        self._metadata = None
        if metadata:
            if isinstance(metadata, dict):
                self._metadata = EventMetadata(**metadata)
            else:
                self._metadata = metadata

    def get_text(self) -> Optional[str]:
        """Get message text.
        
        Returns:
            Message text if available, None otherwise
        """
        return self.update.message_text

    def get_metadata(self) -> EventMetadata:
        """Get event metadata.
        
        Returns:
            Event metadata
        """
        if self._metadata is None:
            metadata = {
                'chat_id': self.update.chat_id,
                'chat_title': self.update.chat_title,
                'sender_id': self.update.sender_id,
                'sender_name': self.update.sender_name,
                'message_id': self.update.message_id,
                'thread_id': self.update.thread_id,
                'timestamp': self.update.timestamp
            }
            self._metadata = EventMetadata(**metadata)
        return self._metadata

    def get_command_args(self) -> list[str]:
        """Get command arguments.
        
        Returns:
            List of command arguments
        """
        text = self.get_text()
        if text and text.startswith('/'):
            parts = text.split()
            if len(parts) > 1:
                return parts[1:]
        return []
