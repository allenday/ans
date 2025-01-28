"""Abstract base class for message senders."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union

from chronicler.logging import get_logger
from chronicler.metadata import EventMetadata
from chronicler.frames.base import Frame

class AbstractSender(ABC):
    """Abstract base class for message senders."""

    def __init__(self):
        """Initialize the sender."""
        self.logger = get_logger(__name__)
        self.logger.debug("SENDER - Initialized AbstractSender")
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the sender."""
        pass

    @abstractmethod
    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to: Optional[int] = None,
        thread_id: Optional[int] = None,
        **kwargs: Dict[str, Any]
    ) -> Optional[Frame]:
        """Send a message to a chat."""
        pass

    @abstractmethod
    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        **kwargs: Dict[str, Any]
    ) -> Optional[Frame]:
        """Edit a message in a chat."""
        pass

    @abstractmethod
    async def delete_message(
        self,
        chat_id: int,
        message_id: int,
        **kwargs: Dict[str, Any]
    ) -> None:
        """Delete a message from a chat."""
        pass

    @abstractmethod
    async def get_chat_title(self, chat_id: int) -> Optional[str]:
        """Get the title of a chat."""
        pass

    @abstractmethod
    async def get_chat_type(self, chat_id: int) -> Optional[str]:
        """Get the type of a chat."""
        pass

    @abstractmethod
    async def get_chat_member_count(self, chat_id: int) -> Optional[int]:
        """Get the number of members in a chat."""
        pass

    @abstractmethod
    async def get_chat_member(
        self,
        chat_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get information about a chat member."""
        pass

    @abstractmethod
    async def get_me(self) -> Optional[Dict[str, Any]]:
        """Get information about the bot."""
        pass 