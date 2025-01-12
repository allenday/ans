"""Storage processor for saving messages."""
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from chronicler.frames import (
    Frame, TextFrame, ImageFrame, DocumentFrame,
    AudioFrame, VoiceFrame, StickerFrame, MediaFrame
)
from chronicler.storage.interface import Message, Attachment, User, Topic
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.processors.base import BaseProcessor
from chronicler.processors.git_processor import GitProcessor
from chronicler.services.git_sync_service import GitSyncService
from chronicler.exceptions import StorageProcessingError

logger = logging.getLogger(__name__)

class StorageProcessor(BaseProcessor):
    """Processor for storing messages and media."""
    
    def __init__(self, storage_path: Path):
        """Initialize storage processor.
        
        Args:
            storage_path: Path to storage directory
        """
        super().__init__()
        self.storage_path = Path(storage_path)
        self.storage = StorageCoordinator(storage_path)
        self.git_processor = None
        self.git_sync_service = None
        self._initialized = False
        
        # Configure git if environment variables are set
        if all(os.getenv(var) for var in ['GIT_REPO_URL', 'GIT_USERNAME', 'GIT_ACCESS_TOKEN']):
            self.git_processor = GitProcessor(
                repo_url=os.getenv('GIT_REPO_URL'),
                branch=os.getenv('GIT_BRANCH', 'main'),
                username=os.getenv('GIT_USERNAME'),
                access_token=os.getenv('GIT_ACCESS_TOKEN'),
                storage_path=storage_path
            )
            
            sync_interval = int(os.getenv('GIT_SYNC_INTERVAL', '300').split('#')[0].strip())
            self.git_sync_service = GitSyncService(
                git_processor=self.git_processor,
                sync_interval=sync_interval
            )
            logger.info("PROC - Configured git integration")
        else:
            logger.info("PROC - Git integration not configured")
    
    async def start(self) -> None:
        """Start the storage processor and git sync service."""
        if not self._initialized:
            logger.info("PROC - Initializing storage with default user")
            user = User(id="default", name="Default User")
            logger.debug(f"PROC - Creating user {user.id} with name {user.name}")
            await self.storage.init_storage(user)
            self._initialized = True
            logger.info("PROC - Storage initialization completed successfully")
        
        if self.git_sync_service:
            await self.git_sync_service.start()
            logger.info("PROC - Started git sync service")
    
    async def stop(self) -> None:
        """Stop the storage processor and git sync service."""
        if self.git_sync_service:
            await self.git_sync_service.stop()
            logger.info("PROC - Stopped git sync service")
    
    async def _commit_message(self, message_path: Path) -> None:
        """Commit a message file if git is configured."""
        if not self.git_sync_service:
            return
        
        try:
            await self.git_sync_service.commit_immediately(message_path)
            logger.info("PROC - Committed message file: %s", message_path)
        except Exception as e:
            logger.error("PROC - Failed to commit message", exc_info=True)
            # Don't re-raise - git failures shouldn't break message processing
    
    async def _commit_media(self, media_paths: list[Path]) -> None:
        """Commit media files if git is configured."""
        if not self.git_sync_service or not media_paths:
            return
        
        try:
            await self.git_sync_service.commit_immediately(media_paths, is_media=True)
            logger.info("PROC - Committed %d media files", len(media_paths))
        except Exception as e:
            logger.error("PROC - Failed to commit media files", exc_info=True)
            # Don't re-raise - git failures shouldn't break message processing
    
    async def _ensure_initialized(self) -> None:
        """Ensure the storage is initialized."""
        if not self._initialized:
            await self.start()
    
    async def process_frame(self, frame: Frame) -> None:
        """Process a frame by saving it to storage."""
        try:
            logger.info(f"PROC - Processing frame of type: {type(frame).__name__}")
            await self._ensure_initialized()
            
            # Extract metadata
            chat_id = frame.metadata.get('chat_id')
            thread_id = frame.metadata.get('thread_id')
            chat_title = frame.metadata.get('chat_title')
            
            if not all([chat_id, thread_id]):
                raise StorageProcessingError("Missing required metadata: chat_id and thread_id")
            
            # Create topic if it doesn't exist
            if not await self.storage.has_topic(thread_id):
                logger.info(f"PROC - Creating new topic with ID: {thread_id}")
                await self.storage.create_topic(
                    topic_id=thread_id,
                    title=chat_title or f"Topic {thread_id}"
                )
            
            # Process based on frame type
            if isinstance(frame, TextFrame):
                await self._process_text_frame(frame, chat_id, thread_id)
            elif isinstance(frame, MediaFrame):
                await self._process_media_frame(frame, chat_id, thread_id)
            else:
                raise StorageProcessingError(f"Unsupported frame type: {type(frame)}")
                
        except Exception as e:
            logger.error(f"PROC - Failed to process frame: {str(e)}", exc_info=True)
            raise StorageProcessingError(f"Failed to process frame: {str(e)}") from e
            
    async def _process_text_frame(self, frame: TextFrame, chat_id: str, thread_id: str) -> None:
        """Process a text frame."""
        try:
            logger.info(f"PROC - Processing text frame for topic {thread_id}")
            metadata = frame.metadata.copy()
            metadata.update({
                'chat_id': chat_id,
                'thread_id': thread_id,
                'source': 'telegram'
            })
            message = Message(
                content=frame.content,
                source='telegram',
                metadata=metadata
            )
            message_path = await self.storage.save_message(thread_id, message)
            logger.info(f"PROC - Saved text message to topic {thread_id}")
            
            # Commit message
            await self._commit_message(message_path)
            
        except Exception as e:
            logger.error(f"PROC - Failed to process text frame: {e}", exc_info=True)
            raise
            
    async def _process_image_frame(self, topic_id: str, frame: ImageFrame, metadata: dict) -> None:
        """Process an image frame."""
        try:
            logger.info(f"PROC - Processing image frame for topic {topic_id}")
            file_id = metadata.get('file_id', f"image_{datetime.utcnow().isoformat()}")
            
            attachment = Attachment(
                id=file_id,
                type=f"image/{frame.format}",
                filename=f"{file_id}.{frame.format}",
                data=frame.content
            )
            logger.debug(f"PROC - Created image attachment: {attachment.filename}")
            
            message = Message(
                content='',
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"PROC - Created message with {len(message.attachments)} attachments")
            
            message_path, media_paths = await self.storage.save_message(topic_id, message)
            logger.info(f"PROC - Saved image message to topic {topic_id}")
            
            # Commit message and media
            await self._commit_message(message_path)
            await self._commit_media(media_paths)
            
        except Exception as e:
            logger.error(f"PROC - Failed to process image frame: {e}", exc_info=True)
            raise
            
    async def _process_document_frame(self, topic_id: str, frame: DocumentFrame, metadata: dict) -> None:
        """Process a document frame."""
        try:
            logger.info(f"PROC - Processing document frame for topic {topic_id}")
            attachment_id = metadata.get('file_unique_id', metadata.get('file_id', 'unknown'))
            logger.debug(f"PROC - Using attachment ID: {attachment_id}")
            
            attachment = Attachment(
                id=attachment_id,
                type=frame.mime_type,
                filename=frame.filename,
                data=frame.content
            )
            logger.debug(f"PROC - Created attachment {attachment.filename} of type {attachment.type}")
            
            message = Message(
                content=frame.caption or '',
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"PROC - Message has {len(message.attachments)} attachments")
            
            message_path = await self.storage.save_message(topic_id, message)
            logger.info(f"PROC - Saved document message to topic {topic_id}")
            
            # Commit message
            await self._commit_message(message_path)
            
        except Exception as e:
            logger.error(f"PROC - Failed to process document frame: {e}", exc_info=True)
            raise

    async def _process_audio_frame(self, topic_id: str, frame: AudioFrame, metadata: dict) -> None:
        """Process an audio frame."""
        try:
            logger.info(f"PROC - Processing audio frame for topic {topic_id}")
            file_id = metadata.get('file_id', f"audio_{datetime.utcnow().isoformat()}")
            
            # Add duration to metadata
            metadata = {**metadata, 'duration': frame.duration}
            
            attachment = Attachment(
                id=file_id,
                type=frame.mime_type,
                filename=f"{file_id}.{frame.mime_type.split('/')[-1]}",
                data=frame.content
            )
            logger.debug(f"PROC - Created audio attachment: {attachment.filename}")
            
            message = Message(
                content='',  # Empty string by default for audio
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"PROC - Created message with {len(message.attachments)} attachments")
            
            message_path = await self.storage.save_message(topic_id, message)
            logger.info(f"PROC - Saved audio message to topic {topic_id}")
            
            # Commit message
            await self._commit_message(message_path)
            
        except Exception as e:
            logger.error(f"PROC - Failed to process audio frame: {e}", exc_info=True)
            raise

    async def _process_voice_frame(self, topic_id: str, frame: VoiceFrame, metadata: dict) -> None:
        """Process a voice frame."""
        try:
            logger.info(f"PROC - Processing voice frame for topic {topic_id}")
            file_id = metadata.get('file_id', f"voice_{datetime.utcnow().isoformat()}")
            
            # Add duration to metadata
            metadata = {**metadata, 'duration': frame.duration}
            
            attachment = Attachment(
                id=file_id,
                type=frame.mime_type,
                filename=f"{file_id}.{frame.mime_type.split('/')[-1]}",
                data=frame.content
            )
            logger.debug(f"PROC - Created voice attachment: {attachment.filename}")
            
            message = Message(
                content='',  # Empty string by default for voice messages
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"PROC - Created message with {len(message.attachments)} attachments")
            
            message_path = await self.storage.save_message(topic_id, message)
            logger.info(f"PROC - Saved voice message to topic {topic_id}")
            
            # Commit message
            await self._commit_message(message_path)
            
        except Exception as e:
            logger.error(f"PROC - Failed to process voice frame: {e}", exc_info=True)
            raise

    async def _process_sticker_frame(self, topic_id: str, frame: StickerFrame, metadata: dict) -> None:
        """Process a sticker frame."""
        try:
            logger.info(f"PROC - Processing sticker frame for topic {topic_id}")
            file_id = metadata.get('file_id', f"sticker_{datetime.utcnow().isoformat()}")
            
            # Add sticker metadata
            metadata = {
                **metadata,
                'emoji': frame.emoji,
                'set_name': frame.set_name
            }
            
            attachment = Attachment(
                id=file_id,
                type="image/webp",  # Stickers are typically WebP format
                filename=f"{file_id}.webp",
                data=frame.content
            )
            logger.debug(f"PROC - Created sticker attachment: {attachment.filename}")
            
            message = Message(
                content=frame.emoji,  # Use emoji as content
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"PROC - Created message with {len(message.attachments)} attachments")
            
            message_path = await self.storage.save_message(topic_id, message)
            logger.info(f"PROC - Saved sticker message to topic {topic_id}")
            
            # Commit message
            await self._commit_message(message_path)
            
        except Exception as e:
            logger.error(f"PROC - Failed to process sticker frame: {e}", exc_info=True)
            raise 

    async def _process_media_frame(self, frame: MediaFrame, chat_id: str, thread_id: str) -> None:
        """Process a media frame."""
        try:
            logger.info(f"PROC - Processing media frame for topic {thread_id}")
            
            # Create attachment based on frame type
            if isinstance(frame, ImageFrame):
                file_id = frame.metadata.get('file_id', f"image_{datetime.utcnow().isoformat()}")
                attachment = Attachment(
                    id=file_id,
                    type=f"image/{frame.format}",
                    filename=f"{file_id}.{frame.format}",
                    data=frame.content
                )
            elif isinstance(frame, DocumentFrame):
                file_id = frame.metadata.get('file_unique_id', frame.metadata.get('file_id', 'unknown'))
                attachment = Attachment(
                    id=file_id,
                    type=frame.mime_type,
                    filename=frame.filename,
                    data=frame.content
                )
            elif isinstance(frame, AudioFrame):
                file_id = frame.metadata.get('file_id', f"audio_{datetime.utcnow().isoformat()}")
                attachment = Attachment(
                    id=file_id,
                    type=frame.mime_type,
                    filename=f"{file_id}.{frame.mime_type.split('/')[-1]}",
                    data=frame.content
                )
            elif isinstance(frame, VoiceFrame):
                file_id = frame.metadata.get('file_id', f"voice_{datetime.utcnow().isoformat()}")
                attachment = Attachment(
                    id=file_id,
                    type=frame.mime_type,
                    filename=f"{file_id}.{frame.mime_type.split('/')[-1]}",
                    data=frame.content
                )
            elif isinstance(frame, StickerFrame):
                file_id = frame.metadata.get('file_id', f"sticker_{datetime.utcnow().isoformat()}")
                attachment = Attachment(
                    id=file_id,
                    type="image/webp",
                    filename=f"{file_id}_{frame.set_name}.webp",
                    data=frame.content
                )
            else:
                raise StorageProcessingError(f"Unsupported media frame type: {type(frame)}")
            
            logger.debug(f"PROC - Created attachment: {attachment.filename}")
            
            # Create message with attachment
            message = Message(
                content=getattr(frame, 'caption', '') or '',
                source='telegram',
                metadata={
                    'chat_id': chat_id,
                    'thread_id': thread_id,
                    'source': 'telegram'
                },
                attachments=[attachment]
            )
            logger.debug(f"PROC - Created message with {len(message.attachments)} attachments")
            
            # Save message and attachments
            message_path, media_paths = await self.storage.save_message(thread_id, message)
            logger.info(f"PROC - Saved media message to topic {thread_id}")
            
            # Commit message and media
            await self._commit_message(message_path)
            await self._commit_media(media_paths)
            
        except Exception as e:
            logger.error(f"PROC - Failed to process media frame: {e}", exc_info=True)
            raise

    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame by saving it to storage.
        
        Args:
            frame: The frame to process
            
        Returns:
            The processed frame or None
        """
        await self.process_frame(frame)
        return frame 