"""Telegram user transport implementation using Telethon."""
import logging
from typing import Optional

from telethon import TelegramClient
from telethon import events

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame
from chronicler.frames.command import CommandFrame
from chronicler.transports.base import BaseTransport
from chronicler.transports.events import TelethonEvent, EventMetadata

logger = logging.getLogger(__name__)

class TelegramUserTransport(BaseTransport):
    """Transport for interacting with Telegram as a user via Telethon."""
    
    def __init__(self, api_id: str, api_hash: str, phone_number: str, session_name: str = "chronicler"):
        super().__init__()
        logger.info("[USER] Initializing TelegramUserTransport")
        
        # Validate parameters
        if not api_id:
            logger.error("[USER] api_id must not be empty")
            raise ValueError("api_id must not be empty")
        if not api_hash:
            logger.error("[USER] api_hash must not be empty")
            raise ValueError("api_hash must not be empty")
        if not phone_number:
            logger.error("[USER] phone_number must not be empty")
            raise ValueError("phone_number must not be empty")
        if not session_name:
            logger.error("[USER] session_name must not be empty")
            raise ValueError("session_name must not be empty")
        
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash)
        self._command_handlers = {}  # Map of command -> handler function
        self._event_handler = None  # Store the event handler
        logger.debug("[USER] Telethon client initialized with session_name=%s", session_name)
    
    async def start(self):
        """Start the Telethon client."""
        await super().start()
        logger.info("[USER] Starting TelegramUserTransport")
        try:
            # Try to start with the existing session
            logger.debug("[USER] Connecting to Telegram")
            await self.client.connect()
            if not await self.client.is_user_authorized():
                # Only prompt for phone verification if not already authorized
                logger.info("[USER] Not authorized, starting phone verification")
                await self.client.start(phone=self.phone_number)
                logger.info("[USER] Phone verification completed")
            else:
                logger.debug("[USER] Already authorized")
                await self.client.start(phone=self.phone_number)
            
            # Register command handler if not already registered
            if not self._event_handler:
                async def command_handler(event):
                    """Handle command event."""
                    wrapped_event = TelethonEvent(event)
                    command = await wrapped_event.get_command()
                    logger.debug(f"[USER] Received command: {command} with args: {await wrapped_event.get_command_args()}")
                    
                    if command is None:
                        logger.debug("[USER] No command found in message")
                        return
                    
                    handler = self._command_handlers.get(command)
                    if not handler:
                        logger.debug(f"[USER] No handler for command: {command}")
                        return
                    
                    # Get chat title if available, otherwise use empty string
                    chat_title = event.chat.title if event.chat and hasattr(event.chat, 'title') else ''
                    
                    # Get sender username if available, otherwise use empty string
                    sender_name = event.sender.username if event.sender and hasattr(event.sender, 'username') else ''
                    
                    metadata = EventMetadata(
                        chat_id=event.chat_id,
                        chat_title=chat_title,
                        sender_id=event.sender_id,
                        sender_name=sender_name,
                        message_id=event.message.id
                    )
                    
                    frame = CommandFrame(
                        metadata=metadata,
                        command=command,
                        args=await wrapped_event.get_command_args()
                    )
                    
                    return await handler(frame)
                
                self._event_handler = self.client.on(events.NewMessage(pattern=r'^/[a-zA-Z]+'))(command_handler)
                logger.debug("[USER] Registered global command event handler")
            
            logger.info("[USER] TelegramUserTransport started successfully")
        except Exception as e:
            self._error_count += 1
            logger.error(f"[USER] Error starting TelegramUserTransport: {str(e)}", exc_info=True)
            raise
    
    async def stop(self):
        """Stop the Telethon client."""
        await super().stop()
        logger.info("[USER] Stopping TelegramUserTransport")
        await self.client.disconnect()
        logger.info("[USER] TelegramUserTransport stopped")
    
    async def process_frame(self, frame: Frame):
        """Process a frame using Telethon client."""
        logger.debug(f"[USER] Processing frame of type {type(frame).__name__}")
        
        if not hasattr(frame, 'metadata') or not isinstance(frame.metadata, EventMetadata):
            logger.error("[USER] Frame missing required EventMetadata")
            self._error_count += 1
            raise ValueError("Frame must have EventMetadata")
        
        chat_id = frame.metadata.chat_id
        
        try:
            if isinstance(frame, TextFrame):
                logger.debug(f"[USER] Processing TextFrame with text: {frame.content}")
                message = await self.client.send_message(
                    chat_id=frame.metadata.chat_id,
                    text=frame.content
                )
                frame.metadata.message_id = message.id
                self._message_count += 1
                logger.debug("[USER] TextFrame sent successfully")
            elif isinstance(frame, ImageFrame):
                logger.debug("[USER] Processing ImageFrame")
                caption = frame.metadata.get('caption', None)
                message = await self.client.send_file(
                    chat_id,
                    file=frame.content,
                    caption=caption
                )
                frame.metadata.message_id = message.id
                self._message_count += 1
                logger.debug("[USER] ImageFrame sent successfully")
            elif isinstance(frame, DocumentFrame):
                logger.debug("[USER] Processing DocumentFrame")
                await self.client.send_file(
                    frame.metadata.chat_id,
                    file=frame.content,
                    caption=frame.caption,
                    force_document=True
                )
                self._message_count += 1
                logger.debug("[USER] DocumentFrame sent successfully")
            else:
                logger.warning(f"[USER] Unsupported frame type: {type(frame).__name__}")
                self._error_count += 1
                raise ValueError(f"Unsupported frame type: {type(frame).__name__}")
        except Exception as e:
            self._error_count += 1
            logger.error(f"[USER] Error processing frame: {str(e)}", exc_info=True)
            raise
    
    async def register_command(self, command: str, handler: callable):
        """Register a command handler."""
        if not command:
            raise ValueError("Command must not be empty")
        if not handler:
            raise ValueError("Handler must not be empty")
        
        self._command_handlers[f"/{command}"] = handler
        logger.debug(f"[USER] Registered handler for command: {command}")
    
    async def send(self, frame: Frame) -> Frame:
        """Send a frame using Telethon."""
        await self.process_frame(frame)
        return frame 