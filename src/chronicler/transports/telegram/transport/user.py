"""Telegram user transport implementation."""

import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable, Union
from telethon import TelegramClient, events
from telethon.tl.types import Message as TelethonMessage
from telethon.errors import ApiIdInvalidError
from datetime import datetime, timezone

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.transports.telegram_transport import TelegramTransportBase
from chronicler.transports.telegram_user_event import TelegramUserEvent
from chronicler.transports.telegram_user_update import TelegramUserUpdate
from chronicler.transports.telegram.message_sender import TelegramMessageSender
from chronicler.transports.events import EventMetadata
from chronicler.logging import get_logger, trace_operation
from chronicler.logging.config import CORRELATION_ID
from chronicler.exceptions import TransportError, TransportAuthenticationError

logger = get_logger(__name__, component='transports.telegram')

class TelegramUserTransport(TelegramTransportBase):
    """Telegram user transport implementation."""

    def __init__(self, api_id: int, api_hash: str, phone_number: str, session_name: str = ":memory:"):
        """Initialize transport.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone_number: User's phone number
            session_name: Name of the session file
            
        Raises:
            TransportAuthenticationError: If any required parameter is empty
        """
        super().__init__()
        if not api_id or not api_hash or not phone_number:
            raise TransportAuthenticationError("API ID, API hash and phone number cannot be empty")
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._session_name = session_name or ":memory:"
        self._client = None
        self._initialized = False
        self._error_count = 0
        self.frame_processor = None
        self._message_sender = None
        self.logger = get_logger(__name__)

    @property
    async def is_running(self) -> bool:
        """Return True if transport is running."""
        if self._client:
            return await self._client.is_connected()
        return False

    async def authenticate(self) -> None:
        """Authenticate with Telegram using the provided credentials.
        
        Raises:
            TransportAuthenticationError: If authentication fails
        """
        try:
            self._client = TelegramClient(self._session_name, self._api_id, self._api_hash)
            await self._client.connect()
            
            if not await self._client.is_user_authorized():
                await self._client.send_code_request(self._phone_number)
                raise TransportAuthenticationError("User not authorized")
                
            me = await self._client.get_me()
            self._message_sender = TelegramMessageSender(self._client)
            self._initialized = True
        except ApiIdInvalidError:
            self._initialized = False
            self._client = None
            raise TransportAuthenticationError("The api_id/api_hash combination is invalid")
        except Exception as e:
            self._initialized = False
            self._client = None
            raise TransportAuthenticationError(f"Failed to authenticate: {str(e)}")

    async def start(self) -> None:
        """Start the transport.
        
        Raises:
            TransportAuthenticationError: If transport is not authenticated.
            TransportError: If transport fails to start.
        """
        if not self._initialized:
            await self.authenticate()
            
        try:
            if not self._client:
                raise TransportAuthenticationError("Transport must be authenticated before starting")
                
            if not await self._client.is_connected():
                await self._client.connect()
                
            if not self._message_sender:
                self._message_sender = TelegramMessageSender(self._client)
                
            await self._client.start()
            self._initialized = True
        except Exception as e:
            self._initialized = False
            raise TransportError(f"Failed to start client: {str(e)}")

    async def stop(self):
        """Stop the transport."""
        if not self._initialized:
            return
            
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting client: {e}")
        self._initialized = False
        self._message_sender = None

    @trace_operation('transport.telegram.user')
    async def send(self, frame: Frame) -> Frame:
        """Send a frame.
        
        Args:
            frame: Frame to send
            
        Returns:
            Frame with updated metadata
            
        Raises:
            TransportError: If sending fails
        """
        if not self._initialized:
            raise RuntimeError("Transport not initialized")

        try:
            result = await self._message_sender.send(frame)
            return result
        except Exception as e:
            raise TransportError(str(e))

    async def _handle_message(self, update: TelegramUserUpdate) -> None:
        """Handle incoming message."""
        if not self._initialized:
            raise RuntimeError("Transport not initialized")

        try:
            metadata = update.get_metadata()
            frame = TextFrame(content=update.message_text, metadata=metadata)
            if self.frame_processor:
                frame = await self.frame_processor(frame)
            if frame:
                await self.send(frame)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            raise

    async def process_frame(self, frame: Frame) -> Frame:
        """Process a frame.
        
        Args:
            frame: Frame to process
            
        Returns:
            Processed frame
        """
        if self.frame_processor:
            try:
                frame = await self.frame_processor(frame)
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                raise
        return frame

    async def register_command(self, command: str, handler):
        """Register command handler."""
        raise NotImplementedError("Command registration is no longer supported in Transport")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        await self.stop()
