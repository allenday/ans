"""Telegram bot transport implementation using python-telegram-bot."""
import logging
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.error import InvalidToken

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame
from chronicler.frames.command import CommandFrame
from chronicler.transports.base import BaseTransport
from chronicler.transports.events import TelegramBotEvent, EventMetadata

logger = logging.getLogger(__name__)

class TelegramBotTransport(BaseTransport):
    """Transport for interacting with Telegram as a bot via python-telegram-bot."""
    
    def __init__(self, token: str):
        super().__init__()
        logger.info("[BOT] Initializing TelegramBotTransport")
        
        if not token:
            logger.error("[BOT] Token must not be empty")
            raise ValueError("Token must not be empty")
        
        self.token = token
        self.app = Application.builder().token(token).build()
        self._command_handlers = {}  # Map of command -> handler function
        logger.debug("[BOT] Application initialized")
    
    async def start(self):
        """Start the bot application."""
        await super().start()
        logger.info("[BOT] Starting TelegramBotTransport")
        try:
            # Start the bot
            await self.app.initialize()
            await self.app.start()
            await self.app.update_bot_data({})
            await self.app.updater.start_polling(drop_pending_updates=False, allowed_updates=['message'])
            
            logger.info("[BOT] TelegramBotTransport started successfully")
        except InvalidToken:
            self._error_count += 1
            logger.error("[BOT] Invalid bot token")
            raise
        except Exception as e:
            self._error_count += 1
            logger.error(f"[BOT] Error starting TelegramBotTransport: {str(e)}", exc_info=True)
            raise
    
    async def stop(self):
        """Stop the bot application."""
        await super().stop()
        logger.info("[BOT] Stopping TelegramBotTransport")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info("[BOT] TelegramBotTransport stopped")
    
    async def process_frame(self, frame: Frame):
        """Process a frame using python-telegram-bot."""
        logger.debug(f"[BOT] Processing frame of type {type(frame).__name__}")
        
        if not hasattr(frame, 'metadata') or not isinstance(frame.metadata, EventMetadata):
            logger.error("[BOT] Frame missing required EventMetadata")
            self._error_count += 1
            raise ValueError("Frame must have EventMetadata")
        
        chat_id = frame.metadata.chat_id
        
        try:
            if isinstance(frame, TextFrame):
                logger.debug(f"[BOT] Processing TextFrame with text: {frame.content}")
                message = await self.app.bot.send_message(
                    chat_id=chat_id,
                    text=frame.content
                )
                frame.metadata.message_id = message.message_id
                self._message_count += 1
                logger.debug("[BOT] TextFrame sent successfully")
            elif isinstance(frame, ImageFrame):
                logger.debug("[BOT] Processing ImageFrame")
                caption = frame.metadata.get('caption', None)
                message = await self.app.bot.send_photo(
                    chat_id=chat_id,
                    photo=frame.content,
                    caption=caption
                )
                frame.metadata.message_id = message.message_id
                self._message_count += 1
                logger.debug("[BOT] ImageFrame sent successfully")
            elif isinstance(frame, DocumentFrame):
                logger.debug("[BOT] Processing DocumentFrame")
                message = await self.app.bot.send_document(
                    chat_id=chat_id,
                    document=frame.content,
                    caption=frame.caption
                )
                frame.metadata.message_id = message.message_id
                self._message_count += 1
                logger.debug("[BOT] DocumentFrame sent successfully")
            else:
                logger.warning(f"[BOT] Unsupported frame type: {type(frame).__name__}")
                self._error_count += 1
                raise ValueError(f"Unsupported frame type: {type(frame).__name__}")
        except Exception as e:
            self._error_count += 1
            logger.error(f"[BOT] Error processing frame: {str(e)}", exc_info=True)
            raise
    
    async def send(self, frame: Frame) -> Frame:
        """Send a frame using the bot."""
        await self.process_frame(frame)
        return frame
    
    async def register_command(self, command: str, handler: callable):
        """Register a command handler."""
        if not command:
            raise ValueError("Command must not be empty")
        if not handler:
            raise ValueError("Handler must not be empty")
        
        async def wrapped_handler(update: Update, context):
            """Wrap the handler to convert Update to CommandFrame."""
            wrapped_event = TelegramBotEvent(update, context)
            metadata = EventMetadata(
                chat_id=update.effective_chat.id,
                chat_title=update.effective_chat.title or '',
                sender_id=update.effective_user.id,
                sender_name=update.effective_user.username or '',
                message_id=update.effective_message.message_id
            )
            
            frame = CommandFrame(
                metadata=metadata,
                command=f"/{command}",
                args=await wrapped_event.get_command_args()
            )
            
            return await handler(frame)
        
        await self.app.add_handler(CommandHandler(command, wrapped_handler))
        self._command_handlers[f"/{command}"] = handler
        logger.debug(f"[BOT] Registered handler for command: {command}") 