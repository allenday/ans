"""Telegram user event implementation."""

from typing import Optional
from chronicler.transports.events import EventBase, EventMetadata
from chronicler.transports.telegram_user_update import TelegramUserUpdate

class TelegramUserEvent(EventBase):
    """Event from Telegram user API."""

    def __init__(self, update: TelegramUserUpdate, metadata: dict | EventMetadata = None):
        """Initialize event.
        
        Args:
            update: Update from Telegram user API
            metadata: Event metadata as dict or EventMetadata object
        """
        self.update = update
        self._metadata = None
        if metadata:
            if isinstance(metadata, dict):
                # Filter out 'type' field
                metadata_copy = metadata.copy()
                metadata_copy.pop('type', None)
                self._metadata = EventMetadata(**metadata_copy)
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
                'timestamp': self.update.timestamp,
                'platform': 'telegram',
                'is_private': self.update.is_private,
                'is_group': self.update.is_group,
                'channel_id': None,
                'guild_id': None,
                'reply_to': None
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
