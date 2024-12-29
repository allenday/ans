from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
import logging

from chronicler.scribe.interface import (
    ScribeInterface,
    ScribeConfig,
    UserSession,
    GroupConfig,
    MessageConverter
)
from chronicler.storage.interface import StorageAdapter, Message

logger = logging.getLogger(__name__)

class TelegramScribe(ScribeInterface):
    """Telegram implementation of the Scribe interface"""
    
    def __init__(self, config: ScribeConfig, storage: StorageAdapter):
        self.config = config
        self.storage = storage
        self.bot = Bot(token=config.telegram_token)
        self.application = Application.builder().token(config.telegram_token).build()
        
        # Add handlers
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,  # Remove ChatType filter to catch all messages
                self._handle_message_wrapper
            )
        )
        self.application.add_handler(
            CommandHandler("start", self._handle_command_wrapper)
        )
        
        # Track active sessions
        self.sessions: dict[int, UserSession] = {}
        
        # Track group configurations
        self.group_configs: dict[int, GroupConfig] = {}
        
        logger.info("TelegramScribe initialized")
    
    async def start(self) -> None:
        """Start the scribe"""
        logger.info("Starting TelegramScribe")
        await self.application.initialize()
        await self.application.start()
        # Start polling in the background
        await self.application.updater.start_polling(allowed_updates=["message"])
        logger.info("TelegramScribe started and polling")
    
    async def stop(self) -> None:
        """Stop the scribe"""
        logger.info("Stopping TelegramScribe")
        try:
            if self.application.updater.running:
                await self.application.updater.stop()
            if self.application.running:
                await self.application.stop()
            await self.application.shutdown()
            logger.info("TelegramScribe stopped")
        except Exception as e:
            logger.error(f"Error stopping TelegramScribe: {e}")
            # Ignore cleanup errors
            pass
    
    async def _handle_message_wrapper(self, update: Update, context) -> None:
        """Wrapper for message handler to catch exceptions"""
        try:
            await self.handle_message(update)
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    async def _handle_command_wrapper(self, update: Update, context) -> None:
        """Wrapper to handle exceptions in command handler"""
        try:
            logger.info(f"Received command: {update.message.text} from chat {update.message.chat.id}")
            await self.handle_command(update)
        except Exception as e:
            logger.error(f"Error handling command: {e}", exc_info=True)
    
    async def _download_file_data(self, file_id: str) -> bytes:
        """Download file data from Telegram"""
        logger.debug(f"Starting download for file_id: {file_id}")
        try:
            file = await self.bot.get_file(file_id)
            logger.debug(f"Got file info: {file}")
            data = await file.download_as_bytearray()
            logger.debug(f"Downloaded {len(data)} bytes")
            return bytes(data)
        except Exception as e:
            logger.error(f"Download failed for file_id {file_id}: {str(e)}")
            raise
    
    async def handle_message(self, update: Update) -> None:
        """Handle incoming message"""
        logger.info(f"Handling message from user {update.message.from_user.id}")
        
        # Convert message to storage format
        storage_message = await MessageConverter.to_storage_message(update.message)
        logger.debug(f"Converted message with {len(storage_message.attachments) if storage_message.attachments else 0} attachments")
        
        # Download file data for attachments
        if storage_message.attachments:
            for attachment in storage_message.attachments:
                # The attachment ID is already the file ID for photos
                file_id = attachment.id
                if file_id:
                    logger.debug(f"Processing attachment: id={file_id}, type={attachment.type}, filename={attachment.filename}")
                    try:
                        attachment.data = await self._download_file_data(file_id)
                        logger.debug(f"Successfully downloaded {len(attachment.data)} bytes for {attachment.filename}")
                    except Exception as e:
                        logger.error(f"Failed to download attachment {attachment.id}: {e}")
                else:
                    logger.warning(f"No file ID found for attachment {attachment.id}")
        
        # Get group config
        group_id = update.message.chat.id
        if group_id not in self.group_configs:
            logger.warning(f"No topic configured for group {group_id}")
            return
            
        group_config = self.group_configs[group_id]
        logger.debug(f"Found group config for {group_id}: topic_id={group_config.topic_id}")
        
        # Save message to storage
        try:
            await self.storage.save_message(group_config.topic_id, storage_message)
            logger.debug("Successfully saved message to storage")
        except Exception as e:
            logger.error(f"Failed to save message: {e}", exc_info=True)
    
    async def handle_command(self, update: Update) -> None:
        """Handle scribe commands"""
        # Basic command handling for now
        if not update.message or not update.message.text:
            return
            
        if update.message.text.startswith("/start"):
            await update.message.reply_text("Scribe started and ready to chronicle messages!")
    
    def configure_group(self, group_id: int, topic_id: str, enabled: bool = True) -> None:
        """Configure a group for chronicling"""
        logger.info(f"Configuring group {group_id} with topic {topic_id}")
        self.group_configs[group_id] = GroupConfig(
            group_id=group_id,
            topic_id=topic_id,
            enabled=enabled
        ) 