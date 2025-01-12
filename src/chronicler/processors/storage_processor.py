"""Storage processor for saving messages."""
from chronicler.logging import get_logger
from pathlib import Path
from datetime import datetime

from chronicler.pipeline import (
    Frame, TextFrame, ImageFrame, DocumentFrame,
    AudioFrame, VoiceFrame, StickerFrame,
    BaseProcessor
)
from chronicler.storage.interface import Message, Attachment, User, Topic
from chronicler.storage.coordinator import StorageCoordinator

logger = get_logger(__name__)

class StorageProcessor(BaseProcessor):
    """Processor that saves messages to storage."""
    
    def __init__(self, storage_path: Path):
        logger.info("Initializing storage processor", extra={"storage_path": str(storage_path)})
        self.storage = StorageCoordinator(storage_path)
        self._initialized = False
        
    async def _ensure_initialized(self) -> None:
        """Ensure storage is initialized."""
        if not self._initialized:
            user = User(id='default', name='Default User')
            try:
                await self.storage.init_storage(user)
                self._initialized = True
                logger.info("Storage initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize storage", exc_info=True)
                raise
        
    async def process_frame(self, frame: Frame) -> None:
        """Process a frame by saving it to storage."""
        try:
            logger.debug("Processing frame", extra={"frame_type": type(frame).__name__})
            await self._ensure_initialized()
            
            # Extract common metadata
            metadata = {
                'type': frame.__class__.__name__.lower(),
                'source': 'telegram'
            }
            
            # Add chat info if available
            if hasattr(frame, 'metadata'):
                metadata.update(frame.metadata)
            
            # Generate topic key
            topic_key = f"{metadata['chat_id']}:{metadata['thread_id']}"
            
            # Ensure topic exists
            topic_id = await self._ensure_topic_exists(metadata)
            
            # Process frame based on type
            frame_processors = {
                TextFrame: self._process_text_frame,
                ImageFrame: self._process_image_frame,
                DocumentFrame: self._process_document_frame,
                AudioFrame: self._process_audio_frame,
                VoiceFrame: self._process_voice_frame,
                StickerFrame: self._process_sticker_frame
            }
            
            processor = frame_processors.get(type(frame))
            if processor:
                await processor(topic_id, frame, metadata)
            else:
                logger.warning("Unsupported frame type", extra={"frame_type": type(frame)})
                
        except Exception as e:
            logger.error("Failed to process frame", exc_info=True, extra={
                'error': str(e),
                'frame_type': type(frame).__name__,
                'processor': 'storage'
            })
            raise
            
    async def _ensure_topic_exists(self, metadata: dict) -> str:
        """Ensure topic exists and return its ID."""
        try:
            logger.info("Ensuring topic exists")
            thread_id = metadata.get('thread_id')
            if not thread_id:
                logger.error("No thread_id in metadata")
                raise ValueError("Message metadata must include thread_id")
                
            logger.debug(f"Using thread_id as topic_id: {thread_id}")
            
            # Create topic if needed
            logger.info(f"Creating new topic: chat='{metadata.get('chat_title')}', chat_id={metadata.get('chat_id')}, thread_id={thread_id}, topic_id={thread_id}")
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
            logger.info(f"Created new topic with ID: {topic_id}")
            return topic_id
            
        except Exception as e:
            logger.error(f"Failed to ensure topic exists", exc_info=True)
            raise
            
    async def _process_text_frame(self, topic_id: str, frame: TextFrame, metadata: dict) -> None:
        """Process a text frame."""
        try:
            logger.info(f"Processing text frame for topic {topic_id}")
            message = Message(
                content=frame.text,
                source='telegram',
                metadata=metadata
            )
            await self.storage.save_message(topic_id, message)
            logger.info(f"Saved text message to topic {topic_id}")
        except Exception as e:
            logger.error(f"Failed to process text frame", exc_info=True)
            raise
            
    async def _process_image_frame(self, topic_id: str, frame: ImageFrame, metadata: dict) -> None:
        """Process an image frame."""
        try:
            logger.info(f"Processing image frame for topic {topic_id}")
            # Get file ID from metadata, fallback to timestamp if not available
            file_id = metadata.get('file_id', f"image_{datetime.utcnow().isoformat()}")
            
            # Create attachment with proper filename
            attachment = Attachment(
                id=file_id,
                type=f"image/{frame.format}",
                filename=f"{file_id}.{frame.format}",
                data=frame.image
            )
            logger.debug(f"Created image attachment: {attachment.filename}")
            
            # Create message with empty string as default content
            message = Message(
                content='',  # Empty string by default for images without captions
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"Created message with {len(message.attachments)} attachments")
            
            await self.storage.save_message(topic_id, message)
            logger.info(f"Saved image message to topic {topic_id}")
        except Exception as e:
            logger.error(f"Failed to process image frame", exc_info=True)
            raise
            
    async def _process_document_frame(self, topic_id: str, frame: DocumentFrame, metadata: dict) -> None:
        """Process a document frame."""
        try:
            logger.info(f"Processing document frame for topic {topic_id}")
            attachment_id = metadata.get('file_unique_id', metadata.get('file_id', 'unknown'))
            logger.debug(f"Using attachment ID: {attachment_id}")
            
            attachment = Attachment(
                id=attachment_id,
                type=frame.mime_type,
                filename=frame.filename,
                data=frame.content
            )
            logger.debug(f"Created attachment {attachment.filename} of type {attachment.type}")
            
            message = Message(
                content=frame.caption or '',
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"Message has {len(message.attachments)} attachments")
            
            await self.storage.save_message(topic_id, message)
            logger.info(f"Saved document message to topic {topic_id}")
        except Exception as e:
            logger.error(f"Failed to process document frame", exc_info=True)
            raise

    async def _process_audio_frame(self, topic_id: str, frame: AudioFrame, metadata: dict) -> None:
        """Process an audio frame."""
        try:
            logger.info(f"Processing audio frame for topic {topic_id}")
            file_id = metadata.get('file_id', f"audio_{datetime.utcnow().isoformat()}")
            
            # Add duration to metadata
            metadata = {**metadata, 'duration': frame.duration}
            
            attachment = Attachment(
                id=file_id,
                type=frame.mime_type,
                filename=f"{file_id}.{frame.mime_type.split('/')[-1]}",
                data=frame.audio
            )
            logger.debug(f"Created audio attachment: {attachment.filename}")
            
            message = Message(
                content='',  # Empty string by default for audio
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"Created message with {len(message.attachments)} attachments")
            
            await self.storage.save_message(topic_id, message)
            logger.info(f"Saved audio message to topic {topic_id}")
        except Exception as e:
            logger.error(f"Failed to process audio frame", exc_info=True)
            raise

    async def _process_voice_frame(self, topic_id: str, frame: VoiceFrame, metadata: dict) -> None:
        """Process a voice frame."""
        try:
            logger.info(f"Processing voice frame for topic {topic_id}")
            file_id = metadata.get('file_id', f"voice_{datetime.utcnow().isoformat()}")
            
            # Add duration to metadata
            metadata = {**metadata, 'duration': frame.duration}
            
            attachment = Attachment(
                id=file_id,
                type=frame.mime_type,
                filename=f"{file_id}.{frame.mime_type.split('/')[-1]}",
                data=frame.audio
            )
            logger.debug(f"Created voice attachment: {attachment.filename}")
            
            message = Message(
                content='',  # Empty string by default for voice messages
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"Created message with {len(message.attachments)} attachments")
            
            await self.storage.save_message(topic_id, message)
            logger.info(f"Saved voice message to topic {topic_id}")
        except Exception as e:
            logger.error(f"Failed to process voice frame", exc_info=True)
            raise

    async def _process_sticker_frame(self, topic_id: str, frame: StickerFrame, metadata: dict) -> None:
        """Process a sticker frame."""
        try:
            logger.info(f"Processing sticker frame for topic {topic_id}")
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
            logger.debug(f"Created sticker attachment: {attachment.filename}")
            
            message = Message(
                content=frame.emoji,  # Use emoji as content
                source='telegram',
                metadata=metadata,
                attachments=[attachment]
            )
            logger.debug(f"Created message with {len(message.attachments)} attachments")
            
            await self.storage.save_message(topic_id, message)
            logger.info(f"Saved sticker message to topic {topic_id}")
        except Exception as e:
            logger.error(f"Failed to process sticker frame", exc_info=True)
            raise 