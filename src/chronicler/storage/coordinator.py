"""Storage coordination."""
from pathlib import Path
from typing import Dict, Any, List, Optional

from chronicler.storage.interface import User, Topic, Message, Attachment, StorageAdapter
from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.filesystem import FileSystemStorage
from chronicler.storage.serializer import MessageSerializer
from chronicler.storage.telegram import TelegramAttachmentHandler
from chronicler.logging import trace_operation, get_logger

logger = get_logger("storage.coordinator")

class StorageCoordinator(StorageAdapter):
    """Coordinates storage operations across multiple backends."""
    
    def __init__(self, storage_path: Path):
        """Initialize storage coordinator."""
        self.storage_path = storage_path
        self.git_storage = GitStorageAdapter(storage_path)
        self.file_storage = FileSystemStorage(storage_path)
        self.serializer = MessageSerializer()
        self.attachment_handler = TelegramAttachmentHandler(storage_path)
        logger.debug("COORD - Initialized StorageCoordinator", extra={
            'context': {'storage_path': str(storage_path)}
        })

    @trace_operation('storage.coordinator')
    async def create_topic(self, topic: Topic) -> str:
        """Create a new topic."""
        try:
            # Create topic in git storage
            await self.git_storage.create_topic(topic)
            
            # Create topic directory in file storage
            await self.file_storage.create_topic(topic)
            
            return topic.id
            
        except Exception as e:
            logger.error(f"COORD - Failed to create topic: {e}", exc_info=True)
            raise

    @trace_operation('storage.coordinator')
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message and its attachments."""
        try:
            # Process attachments first
            if message.attachments:
                processed_attachments = []
                for attachment in message.attachments:
                    processed = await self.attachment_handler.process(attachment)
                    processed_attachments.append(processed)
                message.attachments = processed_attachments

            # Save message content
            await self.git_storage.save_message(topic_id, message)
            
            # Save attachments to filesystem
            if message.attachments:
                for attachment in message.attachments:
                    await self.file_storage.save_attachment(topic_id, attachment)
                    
        except Exception as e:
            logger.error(f"COORD - Failed to save message: {e}", exc_info=True)
            raise 