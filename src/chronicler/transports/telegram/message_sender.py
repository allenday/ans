"""Telegram message sender implementation."""

from typing import Optional, Dict, Any, Union
from telegram import Bot
from telegram.error import TelegramError

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.logging import get_logger
from chronicler.logging.config import trace_operation
from chronicler.exceptions import TransportError

logger = get_logger(__name__)

class TelegramMessageSender:
    """Handles message sending for Telegram transports."""

    def __init__(self, client: Union[Bot, Any]):
        """Initialize sender.
        
        Args:
            client: Bot instance from python-telegram-bot or Telethon client
        """
        self._client = client
        self.logger = get_logger(__name__)

    @trace_operation('transport.telegram.sender')
    async def send(self, frame: Frame) -> Frame:
        """Send a frame.
        
        Args:
            frame: Frame to send
            
        Returns:
            Frame with updated metadata
            
        Raises:
            TransportError: If sending fails
            ValueError: If frame metadata is invalid
        """
        if not frame.metadata or frame.metadata.get("chat_id") is None:
            raise ValueError("chat_id is required")

        try:
            if isinstance(frame, TextFrame):
                message = await self._send_text(frame)
            elif isinstance(frame, ImageFrame):
                message = await self._send_image(frame)
            else:
                raise TransportError(f"Unsupported frame type: {type(frame)}")

            frame.metadata["message_id"] = message.message_id
            return frame
        except TelegramError as e:
            logger.error(f"Failed to send frame: {e}")
            raise TransportError(str(e)) from e
        except Exception as e:
            logger.error(f"Failed to send frame: {e}")
            raise TransportError(str(e)) from e

    async def _send_text(self, frame: TextFrame) -> Any:
        """Send a text frame.
        
        Args:
            frame: Text frame to send
            
        Returns:
            Sent message
        """
        return await self._client.send_message(
            chat_id=frame.metadata["chat_id"],
            text=frame.content,
            reply_to_message_id=frame.metadata.get("thread_id")
        )

    async def _send_image(self, frame: ImageFrame) -> Any:
        """Send an image frame.
        
        Args:
            frame: Image frame to send
            
        Returns:
            Sent message
        """
        return await self._client.send_photo(
            chat_id=frame.metadata["chat_id"],
            photo=frame.content,
            caption=frame.metadata.get("caption"),
            reply_to_message_id=frame.metadata.get("thread_id")
        ) 