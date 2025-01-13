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
        self.attachment_handler = TelegramAttachmentHandler()
        self._initialized = False
        logger.debug("COORD - Initialized StorageCoordinator", extra={
            'context': {'storage_path': str(storage_path)}
        })

    @trace_operation('storage.coordinator')
    async def init_storage(self, user: User) -> 'StorageAdapter':
        """Initialize storage for a user."""
        try:
            await self.git_storage.init_storage(user)
            await self.file_storage.init_storage(user)
            self._initialized = True
            return self
        except Exception as e:
            logger.error(f"COORD - Failed to initialize storage: {e}", exc_info=True)
            raise

    def is_initialized(self) -> bool:
        """Check if storage is initialized."""
        return self._initialized

    @trace_operation('storage.coordinator')
    async def create_topic(self, topic: Topic, ignore_exists: bool = False) -> str:
        """Create a new topic."""
        try:
            # Create topic in git storage
            await self.git_storage.create_topic(topic, ignore_exists)
            
            # Create topic directory in file storage
            await self.file_storage.create_topic(topic, ignore_exists)
            
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

                # Save attachments to filesystem before saving message
                for attachment in message.attachments:
                    await self.file_storage.save_attachment(topic_id, message.id, attachment)

            # Only save message content if all attachments were saved successfully
            await self.git_storage.save_message(topic_id, message)
                    
        except Exception as e:
            logger.error(f"COORD - Failed to save message: {e}", exc_info=True)
            raise

    @trace_operation('storage.coordinator')
    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        """Save an attachment."""
        try:
            # Process attachment
            processed = await self.attachment_handler.process(attachment)
            
            # Save to filesystem
            await self.file_storage.save_attachment(topic_id, message_id, processed)
            
        except Exception as e:
            logger.error(f"COORD - Failed to save attachment: {e}", exc_info=True)
            raise

    @trace_operation('storage.coordinator')
    async def sync(self) -> None:
        """Sync with remote storage."""
        try:
            await self.git_storage.sync()
        except Exception as e:
            logger.error(f"COORD - Failed to sync: {e}", exc_info=True)
            raise

    @trace_operation('storage.coordinator')
    async def set_github_config(self, token: str, repo: str) -> None:
        """Set GitHub configuration."""
        try:
            await self.git_storage.set_github_config(token, repo)
        except Exception as e:
            logger.error(f"COORD - Failed to set GitHub config: {e}", exc_info=True)
            raise 