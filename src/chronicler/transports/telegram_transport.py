"""Telegram transport implementation."""
import abc
import logging
from typing import Optional, Union
from datetime import datetime, timezone
from unittest.mock import MagicMock

from telegram import Bot, Update, Message, Chat, User
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telethon import TelegramClient, events

from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame, StickerFrame, AudioFrame, VoiceFrame
from chronicler.logging import get_logger, trace_operation
from chronicler.processors.command import CommandProcessor
from chronicler.transports.base import BaseTransport

logger = get_logger(__name__, component="telegram_transport")

class TelegramTransportBase(BaseTransport, abc.ABC):
    """Base class for Telegram transports with common functionality."""
    
    @abc.abstractmethod
    async def start(self):
        """Start the transport."""
        pass
    
    @abc.abstractmethod
    async def stop(self):
        """Stop the transport."""
        pass
    
    @abc.abstractmethod
    async def send(self, frame: Frame) -> Frame:
        """Send a frame through the transport."""
        pass
    
    async def push_frame(self, frame: Frame):
        """Push a frame to the frame processor."""
        if self.frame_processor:
            await self.frame_processor.process(frame)
    
    async def _handle_message(self, update: Update, context=None):
        """Handle incoming messages."""
        message = update.message if isinstance(update, Update) else update
        
        # Create metadata
        metadata = {
            'chat_id': message.chat.id,
            'chat_title': message.chat.title or "Private Chat",
            'sender_id': message.from_user.id,
            'sender_name': message.from_user.username or message.from_user.first_name
        }
        
        # Add thread info if present
        thread_id = getattr(message, 'message_thread_id', None)
        if thread_id:
            metadata['thread_id'] = thread_id
            if thread_id == 1:
                metadata['thread_name'] = "General"
            elif hasattr(message, 'forum_topic_created'):
                metadata['thread_name'] = message.forum_topic_created.name
        
        if message.photo:
            photo = message.photo[-1]  # Get highest quality photo
            file = await context.bot.get_file(photo.file_id) if context else None
            
            metadata.update({
                'mime_type': "image/jpeg",
                'file_id': photo.file_id
            })
            
            content = await file.download_as_bytearray() if file else b''
            
            frame = ImageFrame(
                content=content,
                caption=message.caption or "",  # Empty string if no caption
                size=(photo.width, photo.height),
                metadata=metadata
            )
            await self.push_frame(frame)
            
        elif message.sticker:
            sticker = message.sticker
            file = await context.bot.get_file(sticker.file_id) if context else None
            
            metadata.update({
                'mime_type': "image/webp",
                'file_id': sticker.file_id,
                'is_animated': sticker.is_animated,
                'is_video': sticker.is_video
            })
            
            content = await file.download_as_bytearray() if file else b''
            
            frame = StickerFrame(
                content=content,
                emoji=sticker.emoji,
                set_name=sticker.set_name,
                metadata=metadata
            )
            await self.push_frame(frame)
            
        elif message.text:
            frame = TextFrame(
                content=message.text,
                metadata=metadata
            )
            await self.push_frame(frame)
    
    async def _handle_command(self, update: Update, context=None):
        """Handle bot commands."""
        message = update.message if isinstance(update, Update) else update
        
        # Extract command and args
        parts = message.text.split()
        command = parts[0]  # Keep the leading slash
        args = parts[1:]
        
        # Create metadata
        metadata = {
            'chat_id': message.chat.id,
            'chat_title': message.chat.title or "Private Chat",
            'sender_id': message.from_user.id,
            'sender_name': message.from_user.username or message.from_user.first_name
        }
        
        # Create and push command frame
        frame = CommandFrame(command=command, args=args, metadata=metadata)
        await self.push_frame(frame)

class TelegramBotTransport(TelegramTransportBase):
    """A transport for Telegram bots that converts Telegram messages to frames."""
    
    def __init__(self, token: str):
        super().__init__()
        logger.info("Initializing TelegramBotTransport")
        self.token = token
        self.app = Application.builder().token(token).build()
        self.frame_processor = None  # Initialize frame_processor
        
        # Add command handler first
        self.app.add_handler(CommandHandler(
            ["start", "config", "status"],
            self._handle_command
        ))
        logger.debug("Added command handlers")
        
        # Handle all other message types
        self.app.add_handler(MessageHandler(
            filters.ALL,  # Capture all message types
            self._handle_message
        ))
        logger.debug("Added message handler for all message types")
    
    @trace_operation('transport.telegram')
    async def start(self):
        """Start the Telegram bot and message handling."""
        logger.info("Starting Telegram bot transport")
        await self.app.initialize()
        logger.debug("Application initialized")
        
        # Get bot info
        bot = await self.app.bot.get_me()
        logger.info(f"Bot info: id={bot.id}, name={bot.first_name}, username={bot.username}")
        
        await self.app.start()
        logger.debug("Application started")
        await self.app.updater.start_polling(drop_pending_updates=False, allowed_updates=['message'])
        logger.info("Polling started - bot is ready to receive messages")
    
    @trace_operation('transport.telegram')
    async def stop(self):
        """Stop the Telegram bot."""
        logger.info("Stopping Telegram bot transport")
        if self.app.running:
            logger.debug("Stopping updater")
            await self.app.updater.stop()
            logger.debug("Stopping application")
            await self.app.stop()
            logger.info("Telegram bot transport stopped")
        else:
            logger.warning("Attempted to stop non-running application")
    
    @trace_operation('transport.telegram')
    async def send(self, frame: Frame) -> Frame:
        """Send a frame through the bot transport."""
        if isinstance(frame, TextFrame):
            result = await self.app.bot.send_message(
                chat_id=frame.metadata['chat_id'],
                text=frame.content,
                message_thread_id=frame.metadata.get('thread_id')
            )
            frame.metadata['message_id'] = result.message_id
            return frame
            
        elif isinstance(frame, ImageFrame):
            result = await self.app.bot.send_photo(
                chat_id=frame.metadata['chat_id'],
                photo=frame.content,
                caption=frame.caption,
                message_thread_id=frame.metadata.get('thread_id')
            )
            frame.metadata['message_id'] = result.message_id
            return frame
            
        raise TypeError("Unsupported frame type")
    
    @trace_operation('transport.telegram')
    async def process_frame(self, update_data: dict) -> Frame:
        """Process a simulated update for testing.
        
        Args:
            update_data: Dictionary containing simulated update data
            
        Returns:
            The processed frame
        """
        # Create mock objects with proper nesting
        update = MagicMock(spec=Update)
        message = MagicMock(spec=Message)
        chat = MagicMock(spec=Chat)
        user = MagicMock(spec=User)
        
        # Set up chat attributes
        chat.id = update_data['message']['chat']['id']
        chat.title = "Test Chat"
        chat.type = "private"
        message.chat = chat
        
        # Set up user attributes
        user.id = update_data['message']['from']['id']
        user.username = update_data['message']['from'].get('username')
        user.first_name = "Test User"
        message.from_user = user
        
        # Set message attributes
        message.text = update_data['message'].get('text')
        message.date = datetime.now(timezone.utc)
        
        # Set up command entity if it's a command
        if message.text and message.text.startswith('/'):
            entity = MagicMock()
            entity.type = 'bot_command'
            entity.offset = 0
            entity.length = len(message.text.split()[0])
            message.entities = [entity]
        
        update.message = message
        
        # Process the update
        if message.text and message.text.startswith('/'):
            await self._handle_command(update, None)
        else:
            await self._handle_message(update, None)
            
        return None  # The frame is pushed through push_frame

class TelegramUserTransport(TelegramTransportBase):
    """A transport for Telegram users that converts Telegram messages to frames."""
    
    def __init__(self, api_id: str, api_hash: str, phone_number: str, session_name: str):
        super().__init__()
        logger.info("Initializing TelegramUserTransport")
        
        if not api_id:
            raise ValueError("api_id must not be empty")
        if not api_hash:
            raise ValueError("api_hash must not be empty")
        if not phone_number:
            raise ValueError("phone_number must not be empty")
        if not session_name:
            raise ValueError("session_name must not be empty")
        
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash)
    
    @trace_operation('transport.telegram')
    async def start(self):
        """Start the Telegram user client."""
        logger.info("Starting Telegram user transport")
        await self.client.start(phone=self.phone_number)
        
        # Get user info
        me = await self.client.get_me()
        logger.info(f"User info: id={me.id}, name={me.first_name}, username={me.username}")
        
        # Add event handlers
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            await self._handle_message(event.message)
    
    @trace_operation('transport.telegram')
    async def stop(self):
        """Stop the Telegram user client."""
        logger.info("Stopping Telegram user transport")
        await self.client.disconnect()
        logger.info("Telegram user transport stopped")
    
    @trace_operation('transport.telegram')
    async def send(self, frame: Frame) -> Frame:
        """Send a frame through the user transport."""
        if isinstance(frame, TextFrame):
            result = await self.client.send_message(
                chat_id=frame.metadata['chat_id'],
                text=frame.content,
                reply_to=frame.metadata.get('thread_id')
            )
            frame.metadata['message_id'] = result.id
            return frame
            
        elif isinstance(frame, ImageFrame):
            result = await self.client.send_file(
                chat_id=frame.metadata['chat_id'],
                file=frame.content,
                caption=frame.caption,
                reply_to=frame.metadata.get('thread_id'),
                force_document=False
            )
            frame.metadata['message_id'] = result.id
            return frame
            
        raise TypeError("Unsupported frame type") 