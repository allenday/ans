"""Telegram transport factory and implementations."""
from abc import ABC, abstractmethod
import re
from typing import Optional, Callable, Awaitable
import time

from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.error import InvalidToken
from telethon import TelegramClient
from telethon import events

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame
from chronicler.frames.command import CommandFrame
from chronicler.transports.base import BaseTransport
from chronicler.transports.events import TelethonEvent, TelegramBotEvent, EventMetadata
from chronicler.logging import get_logger, trace_operation

logger = get_logger("chronicler.transports.telegram")

class TelegramTransportBase(BaseTransport, ABC):
    """Base class for Telegram transports."""
    
    def __init__(self):
        super().__init__()
        self._start_time = None
        self._message_count = 0
        self._command_count = 0
        self._error_count = 0
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def start(self):
        """Start the transport."""
        self._start_time = time.time()
        logger.info("Starting transport")
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def stop(self):
        """Stop the transport."""
        uptime = time.time() - (self._start_time or time.time())
        logger.info(f"Stopping transport. Stats: uptime={uptime:.2f}s, messages={self._message_count}, commands={self._command_count}, errors={self._error_count}")
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def process_frame(self, frame: Frame):
        """Process a frame."""
        pass
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def send(self, frame: Frame) -> Optional[Frame]:
        """Send a frame."""
        pass
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def register_command(self, command: str, handler: callable):
        """Register a command handler.
        
        Args:
            command: Command string without leading slash (e.g. "start" for /start)
            handler: Async callback function that takes (frame: CommandFrame) as argument
        """
        pass
    
    def get_stats(self) -> dict:
        """Get transport statistics."""
        uptime = time.time() - (self._start_time or time.time())
        return {
            'uptime': f"{uptime:.2f}s",
            'messages': self._message_count,
            'commands': self._command_count,
            'errors': self._error_count
        }

class TelegramUserTransport(TelegramTransportBase):
    """Transport for interacting with Telegram as a user via Telethon."""
    
    def __init__(self, api_id: str, api_hash: str, phone_number: str, session_name: str = "chronicler"):
        super().__init__()
        logger.info("Initializing Telegram user transport")
        
        # Validate parameters
        if not api_id:
            logger.error("Failed to initialize: empty api_id")
            raise ValueError("api_id must not be empty")
        if not api_hash:
            logger.error("Failed to initialize: empty api_hash")
            raise ValueError("api_hash must not be empty")
        if not phone_number:
            logger.error("Failed to initialize: empty phone_number")
            raise ValueError("phone_number must not be empty")
        if not session_name:
            logger.error("Failed to initialize: empty session_name")
            raise ValueError("session_name must not be empty")
        
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash)
        self._command_handlers = {}  # Map of command -> handler function
        self._event_handler = None  # Store the event handler
        logger.debug("Telethon client initialized with session_name=%s", session_name)
    
    @trace_operation('transport.telegram.user')
    async def start(self):
        """Start the Telethon client."""
        await super().start()
        logger.info("Starting Telegram user transport")
        try:
            # Try to start with the existing session
            logger.debug("Connecting to Telegram")
            await self.client.connect()
            if not await self.client.is_user_authorized():
                # Only prompt for phone verification if not already authorized
                logger.info("Not authorized, starting phone verification")
                await self.client.start(phone=self.phone_number)
                logger.info("Phone verification completed")
            else:
                logger.debug("Already authorized")
                await self.client.start(phone=self.phone_number)
            
            # Register command handler if not already registered
            if not self._event_handler:
                async def command_handler(event):
                    wrapped_event = TelethonEvent(event)
                    command = wrapped_event.get_command()
                    
                    self.logger.debug(f"Received command: {command} with args: {wrapped_event.get_command_args()}")
                    handler = self._command_handlers.get(command)
                    if handler:
                        self.logger.debug(f"Found handler for command: {command}")
                        metadata = wrapped_event.get_metadata()
                        frame = CommandFrame(
                            command=command,
                            args=wrapped_event.get_command_args(),
                            metadata=metadata
                        )
                        self.logger.debug(f"Executing handler for command: {command} with frame: {frame}")
                        try:
                            await handler(frame)
                            self._command_count += 1
                            self.logger.debug(f"Handler execution completed for command: {command}")
                        except Exception as e:
                            self._error_count += 1
                            self.logger.error(f"Error executing handler for command {command}", exc_info=True)
                            raise
                    else:
                        self.logger.debug(f"No handler found for command: {command}")
                
                self._event_handler = self.client.on(events.NewMessage(pattern=r'^/[a-zA-Z]+'))(command_handler)
                self.logger.debug("Registered global command event handler")
            
            logger.info("Telegram user transport started successfully")
        except Exception as e:
            self._error_count += 1
            logger.error("Failed to start transport", exc_info=True)
            raise
    
    @trace_operation('transport.telegram.user')
    async def stop(self):
        """Stop the Telethon client."""
        await super().stop()
        logger.info("Stopping Telegram user transport")
        await self.client.disconnect()
        logger.info("Telegram user transport stopped")
    
    @trace_operation('transport.telegram.user')
    async def process_frame(self, frame: Frame):
        """Process a frame using Telethon client."""
        logger.debug("Processing frame", extra={"type": type(frame).__name__})
        
        if not hasattr(frame, 'metadata') or not isinstance(frame.metadata, EventMetadata):
            logger.error("Failed to process frame: missing EventMetadata")
            self._error_count += 1
            raise ValueError("Frame must have EventMetadata")
        
        chat_id = frame.metadata.chat_id
        
        try:
            if isinstance(frame, TextFrame):
                await self.client.send_message(chat_id, frame.text)
                self._message_count += 1
            elif isinstance(frame, ImageFrame):
                await self.client.send_file(
                    chat_id,
                    file=frame.content,
                    caption=frame.caption
                )
                self._message_count += 1
            elif isinstance(frame, DocumentFrame):
                await self.client.send_file(
                    chat_id,
                    file=frame.content,
                    caption=frame.caption,
                    force_document=True
                )
                self._message_count += 1
            else:
                logger.warning("Unsupported frame type", extra={"type": type(frame).__name__})
                self._error_count += 1
                raise ValueError(f"Unsupported frame type: {type(frame).__name__}")
        except Exception as e:
            self._error_count += 1
            logger.error("Failed to process frame", exc_info=True, extra={
                'error': str(e),
                'frame_type': type(frame).__name__,
                'transport': 'user'
            })
            raise
    
    @trace_operation('transport.telegram.user')
    async def send(self, frame: Frame) -> Optional[Frame]:
        """Send a frame using Telethon client and return updated frame with message ID."""
        logger.debug("Sending frame", extra={"type": type(frame).__name__})
        
        if not hasattr(frame, 'metadata') or not isinstance(frame.metadata, EventMetadata):
            logger.error("Failed to send frame: missing EventMetadata")
            self._error_count += 1
            raise ValueError("Frame must have EventMetadata")
        
        chat_id = frame.metadata.chat_id
        
        try:
            if isinstance(frame, TextFrame):
                message = await self.client.send_message(chat_id, frame.text)
                frame.metadata = EventMetadata(
                    chat_id=chat_id,
                    chat_title=frame.metadata.chat_title,
                    sender_id=frame.metadata.sender_id,
                    sender_name=frame.metadata.sender_name,
                    message_id=message.id
                )
                self._message_count += 1
                return frame
            elif isinstance(frame, ImageFrame):
                message = await self.client.send_file(
                    chat_id,
                    file=frame.content,
                    caption=frame.caption
                )
                frame.metadata = EventMetadata(
                    chat_id=chat_id,
                    chat_title=frame.metadata.chat_title,
                    sender_id=frame.metadata.sender_id,
                    sender_name=frame.metadata.sender_name,
                    message_id=message.id
                )
                self._message_count += 1
                return frame
            elif isinstance(frame, DocumentFrame):
                message = await self.client.send_file(
                    chat_id,
                    file=frame.content,
                    caption=frame.caption,
                    force_document=True
                )
                frame.metadata = EventMetadata(
                    chat_id=chat_id,
                    chat_title=frame.metadata.chat_title,
                    sender_id=frame.metadata.sender_id,
                    sender_name=frame.metadata.sender_name,
                    message_id=message.id
                )
                self._message_count += 1
                return frame
            else:
                logger.warning("Unsupported frame type", extra={"type": type(frame).__name__})
                self._error_count += 1
                raise ValueError(f"Unsupported frame type: {type(frame).__name__}")
        except Exception as e:
            self._error_count += 1
            logger.error("Failed to send frame", exc_info=True, extra={
                'error': str(e),
                'frame_type': type(frame).__name__,
                'transport': 'user'
            })
            raise
    
    @trace_operation('transport.telegram.user')
    async def register_command(self, command: str, handler: Callable[[CommandFrame], Awaitable[None]]):
        """Register a command handler.
        
        Args:
            command: Command to register (with or without leading slash)
            handler: Async function to handle the command
        """
        # Ensure command starts with single slash
        command = '/' + command.lstrip('/')
        self._command_handlers[command] = handler
        logger.debug(f"Registered handler for command: {command}")

    async def _handle_command(self, frame: CommandFrame):
        """Handle a command frame.
        
        Args:
            frame: Command frame to handle
            
        Raises:
            ValueError: If command is not registered
        """
        if frame.command in self._command_handlers:
            await self._command_handlers[frame.command](frame)
        else:
            logger.warning(f"Unknown command: {frame.command}")
            raise ValueError(f"Unknown command: {frame.command}")

    async def process_frame(self, frame: Frame):
        """Process a frame.
        
        Args:
            frame: Frame to process
            
        Raises:
            ValueError: If frame type is not supported or frame metadata is invalid
        """
        if not isinstance(frame.metadata, EventMetadata):
            raise ValueError("Frame must have EventMetadata")

        try:
            if isinstance(frame, CommandFrame):
                await self._handle_command(frame)
            elif isinstance(frame, (TextFrame, ImageFrame)):
                await self.send(frame)
            else:
                raise ValueError(f"Unsupported frame type: {type(frame)}")
        except Exception as e:
            logger.error(f"Failed to process frame: {e}")
            raise

class TelegramBotTransport(TelegramTransportBase):
    """Telegram bot transport implementation."""

    def __init__(self, token: str):
        """Initialize the bot transport.
        
        Args:
            token: Bot token
        """
        super().__init__()
        self._token = token
        self._app = None
        self._command_handlers = {}
        self._initialized = False

    @property
    def token(self) -> str:
        return self._token

    async def register_command(self, command: str, handler: Callable[[CommandFrame], Awaitable[None]]) -> None:
        """Register a command handler.

        Args:
            command: Command to register (without leading slash)
            handler: Handler function to call when command is received
        """
        if not command.startswith('/'):
            command = f'/{command}'
        self._command_handlers[command] = handler
        self.logger.debug(f"Registered command handler for {command}")

    async def start(self) -> None:
        """Start the transport."""
        await super().start()
        self._app = Application.builder().token(self._token).build()
        await self._app.initialize()
        await self._app.start()
        self._initialized = True
        self.logger.info("Bot transport started")

    async def stop(self) -> None:
        """Stop the transport."""
        if self._initialized:
            await self._app.stop()
            await self._app.shutdown()
            self._initialized = False
        await super().stop()
        self.logger.info("Bot transport stopped")

    async def process_frame(self, frame: Frame) -> Frame:
        """Process a frame.

        Args:
            frame: Frame to process

        Returns:
            Processed frame

        Raises:
            ValueError: If frame type is not supported
            RuntimeError: If transport is not initialized
        """
        if not self._initialized:
            await self.start()

        if isinstance(frame, CommandFrame):
            command = frame.command
            if command not in self._command_handlers:
                raise ValueError(f"Command not found: {command}")
            await self._command_handlers[command](frame)
            return frame

        raise ValueError(f"Unsupported frame type: {type(frame).__name__}")

    async def send(self, frame: Frame) -> Frame:
        """Send a frame.

        Args:
            frame: Frame to send

        Returns:
            Frame with updated metadata

        Raises:
            ValueError: If frame type is not supported
            RuntimeError: If transport is not initialized
        """
        if not self._initialized:
            await self.start()

        try:
            if isinstance(frame, TextFrame):
                message = await self._app.bot.send_message(
                    chat_id=frame.metadata.chat_id,
                    text=frame.text
                )
                frame.metadata.message_id = message.message_id
                return frame

            if isinstance(frame, ImageFrame):
                message = await self._app.bot.send_photo(
                    chat_id=frame.metadata.chat_id,
                    photo=frame.content,
                    caption=frame.caption
                )
                frame.metadata.message_id = message.message_id
                return frame

            raise ValueError(f"Unsupported frame type: {type(frame).__name__}")

        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            raise Exception("Failed to send message") from e

class TelegramTransportFactory:
    """Factory for creating Telegram transports."""
    
    def create_transport(
        self,
        bot_token: Optional[str] = None,
        api_id: Optional[str] = None,
        api_hash: Optional[str] = None,
        phone_number: Optional[str] = None,
        session_name: Optional[str] = None
    ) -> TelegramTransportBase:
        """Create a Telegram transport.
        
        Args:
            bot_token: Bot token for bot transport
            api_id: API ID for user transport
            api_hash: API hash for user transport
            phone_number: Phone number for user transport
            session_name: Session name for user transport (default: "chronicler")
        
        Returns:
            A Telegram transport instance
            
        Raises:
            ValueError: If invalid parameter combination is provided
        """
        logger.debug("Creating Telegram transport")
        
        # Check for invalid parameter combinations
        has_bot_token = bool(bot_token)
        has_user_creds = all([api_id, api_hash, phone_number])
        
        if has_bot_token and has_user_creds:
            logger.error("Cannot provide both bot_token and user credentials")
            raise ValueError("Cannot provide both bot_token and user credentials")
        
        if not has_bot_token and not has_user_creds:
            logger.error("Must provide either bot_token or (api_id, api_hash, phone_number)")
            raise ValueError("Must provide either bot_token or (api_id, api_hash, phone_number)")
        
        # Create appropriate transport
        if has_bot_token:
            logger.info("Creating TelegramBotTransport")
            return TelegramBotTransport(token=bot_token)
        else:
            logger.info("Creating TelegramUserTransport")
            return TelegramUserTransport(
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone_number,
                session_name=session_name or "chronicler"
            ) 