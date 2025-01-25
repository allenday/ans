"""Telegram bot transport implementation."""

from typing import Optional, Dict, Any, Callable, Awaitable, Union
from telegram import Update as TelegramUpdate
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ApplicationBuilder
from telegram.error import InvalidToken

from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.transports.telegram_transport import TelegramTransportBase
from chronicler.transports.telegram_bot_event import TelegramBotEvent
from chronicler.transports.telegram_bot_update import TelegramBotUpdate
from chronicler.logging import get_logger
from chronicler.logging.config import trace_operation
from chronicler.exceptions import TransportError, TransportAuthenticationError

logger = get_logger(__name__)

class TelegramBotTransport(TelegramTransportBase):
    """Transport implementation for Telegram Bot API."""

    def __init__(self, token: str):
        """Initialize bot transport.
        
        Args:
            token: Bot token from BotFather.
        """
        super().__init__()
        self._token = token
        self._initialized = False
        self._app = None
        self._bot = None
        self._command_handlers: Dict[str, Callable[[TelegramBotEvent], Awaitable[None]]] = {}
        self.frame_processor = None

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

        if not frame.metadata or frame.metadata.get("chat_id") is None:
            raise ValueError("chat_id is required")

        try:
            if not isinstance(frame, (TextFrame, ImageFrame)):
                raise TransportError(f"Unsupported frame type: {type(frame)}")

            if isinstance(frame, TextFrame):
                message = await self._bot.send_message(
                    chat_id=frame.metadata["chat_id"],
                    text=frame.content,
                    reply_to_message_id=frame.metadata.get("thread_id")
                )
                frame.metadata["message_id"] = message.message_id
            else:  # Must be ImageFrame
                message = await self._bot.send_photo(
                    chat_id=frame.metadata["chat_id"],
                    photo=frame.content,
                    caption=frame.metadata.get("caption"),
                    reply_to_message_id=frame.metadata.get("thread_id")
                )
                frame.metadata["message_id"] = message.message_id

            return frame
        except Exception as e:
            logger.error(f"Failed to send frame: {e}")
            raise TransportError(str(e)) from e

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
            TransportError: If command registration fails
        """
        # Ensure command starts with slash
        cmd_with_slash = f"/{command.lstrip('/')}"
        cmd_without_slash = command.lstrip('/')
        
        # Store handler with slash prefix
        self._command_handlers[cmd_with_slash] = handler
        
        try:
            # Register command handler without slash prefix
            await self._app.add_handler(CommandHandler(
                cmd_without_slash,
                lambda update, context: self._handle_command(update, handler)
            ))
        except Exception as e:
            self.logger.error(f"Failed to register command: {e}")
            # Remove handler since registration failed
            del self._command_handlers[cmd_with_slash]
            raise TransportError(f"Failed to register command: {e}")

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

    async def _handle_command(self, update: Union[TelegramUpdate, CommandFrame], handler: Callable[[TelegramBotEvent], Awaitable[None]]):
        """Handle incoming command."""
        try:
            # If update is already a CommandFrame, use it directly
            if isinstance(update, CommandFrame):
                frame = update
            else:
                # Create command frame from the raw update
                frame = CommandFrame(
                    command=update.message.text.split()[0],  # First word is command
                    args=update.message.text.split()[1:],  # Rest are args
                    metadata={
                        "chat_id": update.message.chat.id,
                        "chat_title": update.message.chat.title,
                        "sender_id": update.message.from_user.id,
                        "sender_name": update.message.from_user.username,
                        "message_id": update.message.message_id,
                        "is_private": update.message.chat.type == "private",
                        "is_group": update.message.chat.type in ["group", "supergroup"]
                    }
                )
            # Process frame
            processed_frame = await self.process_frame(frame)
            # Execute handler
            await handler(processed_frame)
        except Exception as e:
            self.logger.error(f"Failed to handle command: {e}")
            raise TransportError(f"Failed to handle command: {e}")

