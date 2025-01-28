"""Telegram bot transport implementation."""

from typing import Optional, Dict, Any, Callable, Awaitable, Union
from telegram import Update as TelegramUpdate, Message, Chat, User, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ApplicationBuilder
from telegram.error import InvalidToken
from datetime import datetime
import asyncio

from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.transports.telegram_transport import TelegramTransportBase
from chronicler.transports.telegram_bot_event import TelegramBotEvent
from chronicler.transports.telegram_bot_update import TelegramBotUpdate
from chronicler.transports.telegram.message_sender import TelegramMessageSender
from chronicler.logging import get_logger
from chronicler.logging.config import trace_operation, CORRELATION_ID
from chronicler.exceptions import TransportError, TransportAuthenticationError

logger = get_logger(__name__)

class TelegramBotTransport(TelegramTransportBase):
    """Telegram bot transport implementation."""

    def __init__(self, token: str, storage=None):
        """Initialize transport.
        
        Args:
            token: Bot token from BotFather
            storage: Storage instance for saving messages
        """
        super().__init__()
        self._token = token
        self._app = None
        self._bot = None
        self._initialized = False
        self._error_count = 0
        self.frame_processor = None
        self.storage = storage
        self._message_sender = None
        self.logger = get_logger(__name__)

    @property
    def is_running(self) -> bool:
        """Return True if transport is running."""
        return self._initialized

    async def authenticate(self) -> None:
        """Authenticate with Telegram using the provided token.
        
        Raises:
            TransportAuthenticationError: If token is invalid or authentication fails.
        """
        self.logger.debug("Starting authentication")
        
        if not self._token:
            self.logger.error("Empty token provided")
            raise TransportAuthenticationError("Invalid token: You must pass the token you received from https://t.me/Botfather!")
        
        self.logger.debug(f"Attempting to authenticate with token: {self._token}")
        
        # Step 1: Create builder and validate token
        try:
            builder = ApplicationBuilder()
            builder.token(self._token)
        except InvalidToken as e:
            self.logger.error(f"Invalid token error: {e}")
            self._initialized = False
            self._app = None
            raise TransportAuthenticationError(str(e))
        
        # Step 2: Build application
        try:
            self._app = builder.build()
        except InvalidToken as e:
            self.logger.error(f"Invalid token error during build: {e}")
            self._initialized = False
            self._app = None
            raise TransportAuthenticationError(str(e))
        except Exception as e:
            self.logger.error(f"Failed to build application: {e}")
            self._initialized = False
            self._app = None
            raise TransportAuthenticationError(f"Failed to build application: {e}")
        
        # Step 3: Initialize and verify bot
        try:
            await self._app.initialize()
            await self._app.bot.get_me()
            
            self._initialized = True
            self._bot = self._app.bot
            self._message_sender = TelegramMessageSender(self._bot)
            self.logger.debug("Authentication successful")
        except InvalidToken as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            self._initialized = False
            self._app = None
            raise TransportAuthenticationError("Token validation failed")
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            self._initialized = False
            self._app = None
            raise TransportAuthenticationError(f"Failed to initialize bot: {e}")

    async def start(self) -> None:
        """Start the transport.
        
        Raises:
            TransportAuthenticationError: If transport is not authenticated.
            TransportError: If transport fails to start.
        """
        if not self._app:
            raise TransportAuthenticationError("Transport must be authenticated before starting")
            
        try:
            await self._app.start()
            await self._app.add_handler(MessageHandler(filters.ALL, self._handle_message))
            self._initialized = True  # Set initialized after successful start
        except Exception as e:
            self._initialized = False  # Ensure initialized is False on failure
            raise TransportError(f"Failed to start bot: {str(e)}")

    async def stop(self):
        """Stop the transport."""
        if not self._initialized:
            return
            
        if self._app:
            await self._app.stop()
            await self._app.shutdown()
        self._initialized = False

    @trace_operation('transport.telegram.bot')
    async def send(self, frame: Frame) -> Frame:
        """Send a frame.
        
        Args:
            frame: Frame to send
            
        Returns:
            Frame with updated metadata
        """
        if not self._initialized:
            raise RuntimeError("Transport not initialized")

        if not self._message_sender:
            raise RuntimeError("Message sender not initialized")

        return await self._message_sender.send(frame)

    @trace_operation('transport.telegram.bot')
    async def process_frame(self, frame: Frame) -> Frame:
        """Process a frame.
        
        Args:
            frame: Frame to process
            
        Returns:
            Processed frame
        """
        if self.frame_processor:
            return await self.frame_processor(frame)
        return frame

    async def register_command(self, command: str, handler: Callable[[TelegramBotEvent], Awaitable[None]]):
        """Register a command handler.
        
        Args:
            command: Command to handle (with or without leading slash)
            handler: Handler function
            
        Raises:
            NotImplementedError: Command registration is no longer supported in Transport
        """
        raise NotImplementedError("Command registration is no longer supported in Transport")

    async def _handle_message(self, update: TelegramBotUpdate):
        """Handle incoming text messages."""
        event = TelegramBotEvent(update=update)
        
        frame = TextFrame(
            content=update.message_text,
            metadata=event.get_metadata()
        )
        
        try:
            processed_frame = await self.process_frame(frame)
            if processed_frame:
                await self.send(processed_frame)
        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
            self._error_count += 1

