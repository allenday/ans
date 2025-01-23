"""Telegram user transport implementation."""

from typing import Optional, Dict, Any, Callable, Awaitable
from telethon import TelegramClient
from telethon.events import NewMessage
from telethon.errors import ApiIdInvalidError

from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.transports.telegram_transport import TelegramTransportBase
from chronicler.transports.telegram_user_event import TelegramUserEvent
from chronicler.transports.telegram_user_update import TelegramUserUpdate
from chronicler.logging import get_logger
from chronicler.exceptions import TransportError

logger = get_logger(__name__)

class TelegramUserTransport(TelegramTransportBase):
    """Transport implementation for Telegram User API."""

    def __init__(self, api_id: str, api_hash: str, phone_number: str, session_name: str = None):
        """Initialize user transport.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone_number: Phone number for authentication
            session_name: Optional session name
        """
        super().__init__()
        if not api_id or not api_hash or not phone_number:
            raise ValueError("API ID, API hash and phone number cannot be empty")
            
        self._api_id = int(api_id)  # Convert to integer
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._session_name = str(session_name) if session_name else ":memory:"  # Use in-memory session by default
        self._client: Optional[TelegramClient] = None
        self._initialized = False
        self._command_handlers: Dict[str, Callable[[TelegramUserEvent], Awaitable[None]]] = {}
        self.frame_processor = None

    async def start(self):
        """Start the transport."""
        if self._initialized:
            return

        try:
            self._client = TelegramClient(self._session_name, self._api_id, self._api_hash)
            await self._client.connect()
            
            if not await self._client.is_user_authorized():
                await self._client.send_code_request(self._phone_number)
                raise RuntimeError("User not authorized. Please complete authentication flow.")
            
            self._me = await self._client.get_me()
            
            # Register message handler
            async def message_handler(event):
                """Handle incoming messages."""
                if event.message.text and event.message.text.startswith('/'):
                    await self._handle_command(TelegramUserUpdate(event))
                else:
                    await self._handle_message(TelegramUserUpdate(event))
                    
            self._client.add_event_handler(message_handler, NewMessage)
            
            self._initialized = True
            logger.info("User transport started")
            
        except Exception as e:
            logger.error(f"Failed to start user transport: {e}")
            if self._client:
                await self._client.disconnect()
            raise

    async def stop(self):
        """Stop the transport."""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
        await super().stop()

    async def send(self, frame: Frame) -> Frame:
        """Send a frame.
        
        Args:
            frame: Frame to send
            
        Returns:
            Frame with updated metadata
        """
        if not self._initialized:
            raise RuntimeError("Transport not initialized")
            
        try:
            if isinstance(frame, TextFrame):
                message = await self._client.send_message(
                    frame.metadata["chat_id"],
                    frame.content,
                    reply_to=frame.metadata.get("thread_id")
                )
                frame.metadata["message_id"] = message.id
            elif isinstance(frame, ImageFrame):
                message = await self._client.send_file(
                    frame.metadata["chat_id"],
                    file=frame.content,
                    caption=frame.caption if hasattr(frame, 'caption') else None,
                    reply_to=frame.metadata.get("thread_id")
                )
                frame.metadata["message_id"] = message.id
            else:
                raise TransportError(f"Unsupported frame type: {type(frame)}")
                
            return frame
        except Exception as e:
            logger.error(f"Failed to send frame: {e}")
            raise TransportError(str(e)) from e

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

    async def register_command(self, command: str, handler: Callable[[TelegramUserEvent], Awaitable[None]]):
        """Register a command handler.
        
        Args:
            command: Command to handle
            handler: Handler function
        """
        self._command_handlers[command] = handler

    async def _handle_message(self, update: TelegramUserUpdate):
        """Handle incoming text messages."""
        event = TelegramUserEvent(update=update)
        
        frame = TextFrame(
            content=update.message_text,
            metadata=event.get_metadata()
        )
        
        processed_frame = await self.process_frame(frame)
        if processed_frame:
            await self.send(processed_frame)

    async def _handle_command(self, update: TelegramUserUpdate):
        """Handle command messages."""
        event = TelegramUserEvent(update=update)
        
        command = update.message_text.split()[0]  # Keep leading '/'
        if command in self._command_handlers:
            # Create command frame
            metadata = event.get_metadata()
            frame = CommandFrame(
                command=command,
                args=event.get_command_args(),
                metadata=metadata.__dict__
            )
            # Process command frame
            processed_frame = await self.process_frame(frame)
            if processed_frame:
                # Update event with processed frame's arguments
                event = TelegramUserEvent(
                    update=update,
                    metadata=processed_frame.metadata
                )
                # Update command args from processed frame
                event.get_command_args = lambda: processed_frame.args
                await self._command_handlers[command](event)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        await self.stop()
