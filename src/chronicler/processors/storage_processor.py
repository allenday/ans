"""Storage processor for saving messages."""
import logging
from pathlib import Path
from datetime import datetime

from chronicler.pipeline import Frame, TextFrame, ImageFrame, DocumentFrame, BaseProcessor
from chronicler.storage.interface import Message, Attachment, User, Topic
from chronicler.storage.coordinator import StorageCoordinator

logger = logging.getLogger(__name__)

class StorageProcessor(BaseProcessor):
    """Processor that saves messages to storage."""
    
    def __init__(self, storage_path: Path):
        logger.info(f"PROC - Initializing storage processor with path: {storage_path}")
        self.storage = StorageCoordinator(storage_path)
        self._initialized = False
        
    async def _ensure_initialized(self) -> None:
        """Ensure storage is initialized."""
        if not self._initialized:
            logger.info("PROC - Initializing storage with default user")
            user = User(id='default', name='Default User')
            logger.debug("PROC - Creating user default with name Default User")
            try:
                await self.storage.init_storage(user)
                self._initialized = True
                logger.info("PROC - Storage initialization completed successfully")
            except Exception as e:
                logger.error(f"PROC - Failed to initialize storage: {e}", exc_info=True)
                raise
        
    async def process_frame(self, frame: Frame) -> None:
        """Process a frame by saving it to storage."""
        try:
            logger.info(f"PROC - Processing frame of type: {type(frame).__name__}")
            await self._ensure_initialized()
            
            # Extract common metadata
            metadata = {
                'type': frame.__class__.__name__.lower(),
                'source': 'telegram'
            }
            
            # Add chat info if available
            if hasattr(frame, 'metadata'):
                metadata.update(frame.metadata)
                logger.debug(f"PROC - Frame metadata - chat_id: {metadata.get('chat_id')}, title: {metadata.get('chat_title')}, thread_id: {metadata.get('thread_id')}")
            
            # Generate topic key
            topic_key = f"{metadata['chat_id']}:{metadata['thread_id']}"
            logger.debug(f"PROC - Generated topic key: {topic_key}")
            
            # Ensure topic exists
            logger.info(f"PROC - Ensuring topic exists for key: {topic_key}")
            topic_id = await self._ensure_topic_exists(metadata)
            logger.info(f"PROC - Using topic ID: {topic_id}")
            
            # Process frame based on type
            if isinstance(frame, TextFrame):
                logger.info("PROC - Processing text frame")
                await self._process_text_frame(topic_id, frame, metadata)
            elif isinstance(frame, ImageFrame):
                logger.info("PROC - Processing image frame")
                await self._process_image_frame(topic_id, frame, metadata)
            elif isinstance(frame, DocumentFrame):
                logger.info("PROC - Processing document frame")
                await self._process_document_frame(topic_id, frame, metadata)
            else:
                logger.warning(f"PROC - Unsupported frame type: {type(frame)}")
                
        except Exception as e:
            logger.error(f"PROC - Failed to process frame: {e}", exc_info=True)
            raise
            
    async def _ensure_topic_exists(self, metadata: dict) -> str:
        """Ensure topic exists and return its ID."""
        try:
            logger.info("PROC - Ensuring topic exists")
            thread_id = metadata.get('thread_id')
            if not thread_id:
                logger.error("PROC - No thread_id in metadata")
                raise ValueError("Message metadata must include thread_id")
                
            logger.debug(f"PROC - Using thread_id as topic_id: {thread_id}")
            
            # Create topic if needed
            logger.info(f"PROC - Creating new topic: chat='{metadata.get('chat_title')}', chat_id={metadata.get('chat_id')}, thread_id={thread_id}, topic_id={thread_id}")
            topic = Topic(
                id=thread_id,
                name=metadata.get('chat_title', 'Unknown'),
                metadata={
                    'source': metadata['source'],
                    'chat_id': metadata['chat_id'],
                    'thread_id': thread_id
                }
            )
            topic_id = await self.storage.create_topic(topic)
            logger.info(f"PROC - Created new topic with ID: {topic_id}")
            return topic_id
            
        except Exception as e:
            logger.error(f"PROC - Failed to ensure topic exists: {e}", exc_info=True)
            raise
            
    async def _process_text_frame(self, topic_id: str, frame: TextFrame, metadata: dict) -> None:
        """Process a text frame."""
        try:
            logger.info(f"PROC - Processing text frame for topic {topic_id}")
            message = Message(
                content=frame.text,
                source='telegram',
                metadata=metadata
            )
            await self.storage.save_message(topic_id, message)
            logger.info(f"PROC - Saved text message to topic {topic_id}")
        except Exception as e:
            logger.error(f"PROC - Failed to process text frame: {e}", exc_info=True)
            raise
            
    async def _process_image_frame(self, topic_id: str, frame: ImageFrame, metadata: dict) -> None:
        """Process an image frame."""
        try:
            logger.info(f"PROC - Processing image frame for topic {topic_id}")
            # Get file ID from metadata, fallback to timestamp if not available
            file_id = metadata.get('file_id', f"image_{datetime.utcnow().isoformat()}")
            
            # Create attachment with proper filename
            attachment = Attachment(
                id=file_id,
                type=f"image/{frame.format}",
                filename=f"{file_id}.{frame.format}",
                data=frame.image
            )
            logger.debug(f"PROC - Created image attachment: {attachment.filename}")
            
            # Create message with empty string as default content
            message = Message(
                content='',  # Empty string by default for images without captions
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"PROC - Created message with {len(message.attachments)} attachments")
            
            await self.storage.save_message(topic_id, message)
            logger.info(f"PROC - Saved image message to topic {topic_id}")
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
            
            await self.storage.save_message(topic_id, message)
            logger.info(f"PROC - Saved document message to topic {topic_id}")
        except Exception as e:
            logger.error(f"PROC - Failed to process document frame: {e}", exc_info=True)
            raise 