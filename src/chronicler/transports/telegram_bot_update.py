"""Telegram bot update wrapper."""

from typing import Optional
from telegram import Update as TelegramUpdate
from chronicler.transports.events import Update

class TelegramBotUpdate(Update):
    """Wrapper for python-telegram-bot Update."""
    
    def __init__(self, update: TelegramUpdate):
        """Initialize update wrapper.
        
        Args:
            update: Update from python-telegram-bot
        """
        super().__init__(update)
        self._update = update
        
    @property
    def message_text(self) -> Optional[str]:
        """Get message text."""
        if self._update.message:
            return self._update.message.text
        return None
        
    @property
    def chat_id(self) -> int:
        """Get chat ID."""
        return self._update.message.chat.id
        
    @property
    def chat_title(self) -> Optional[str]:
        """Get chat title."""
        if self._update.message.chat.title:
            return self._update.message.chat.title
        return None
        
    @property
    def sender_id(self) -> Optional[int]:
        """Get sender ID."""
        if self._update.message.from_user:
            return self._update.message.from_user.id
        return None
        
    @property
    def sender_name(self) -> Optional[str]:
        """Get sender name."""
        if self._update.message.from_user:
            return self._update.message.from_user.username
        return None
        
    @property
    def message_id(self) -> Optional[int]:
        """Get message ID."""
        return self._update.message.message_id
        
    @property
    def thread_id(self) -> Optional[str]:
        """Get thread ID."""
        if hasattr(self._update.message, 'message_thread_id'):
            return str(self._update.message.message_thread_id)
        return None
        
    @property
    def timestamp(self) -> Optional[float]:
        """Get message timestamp."""
        if self._update.message.date:
            return self._update.message.date.timestamp()
        return None

    @property
    def is_private(self) -> bool:
        """Check if chat is private."""
        if self._update.message and self._update.message.chat:
            return self._update.message.chat.type == 'private'
        return False

    @property
    def is_group(self) -> bool:
        """Check if chat is a group."""
        if self._update.message and self._update.message.chat:
            return self._update.message.chat.type in ('group', 'supergroup')
        return False 