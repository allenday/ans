"""Storage processor for saving messages."""
import logging
from pathlib import Path
from typing import Optional, Union

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame, AudioFrame, VoiceFrame, StickerFrame
from chronicler.processors.base import BaseProcessor
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.exceptions import (
    StorageError, StorageInitializationError,
    StorageOperationError, StorageValidationError,
    ProcessorValidationError
)

logger = logging.getLogger(__name__)

class StorageProcessor(BaseProcessor):
    """Processor that saves messages to storage."""
    
    def __init__(self, coordinator: StorageCoordinator):
        """Initialize the storage processor.

        Args:
            coordinator: StorageCoordinator instance
        """
        super().__init__()
        self.coordinator = coordinator
        self.logger = logger.getChild(self.__class__.__name__)
        self.logger.info("Initializing storage processor")
        
        self._initialized = False
        
    def stop(self) -> None:
        """Stop the storage processor and clean up resources."""
        self.logger.info("Stopping storage processor")
        if hasattr(self.coordinator, 'stop'):
            self.coordinator.stop()
        self._initialized = False
        
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame."""
        try:
            return await self.process_frame(frame)
        except Exception as e:
            logger.error(f"Failed to process frame: {str(e)}")
            raise
        
    async def _ensure_initialized(self) -> None:
        """Ensure storage is initialized."""
        if not self._initialized:
            try:
                await self.coordinator.init_storage(123)  # Use a default user ID
                self._initialized = True
                logger.info("Storage initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize storage: {e}")
                raise StorageInitializationError(str(e))
            
    def _validate_metadata(self, metadata: dict) -> None:
        """Validate frame metadata."""
        required_fields = ['chat_id', 'thread_id']
        for field in required_fields:
            if field not in metadata:
                raise StorageValidationError(f"Message metadata must include {field}")
                
    def _ensure_topic_exists(self, metadata: dict) -> str:
        """Ensure topic exists and return topic ID."""
        chat_id = metadata['chat_id']
        thread_id = metadata['thread_id']
        topic_name = f"{chat_id}:{thread_id}"
        
        if not self.coordinator.topic_exists(topic_name):
            self.coordinator.create_topic(chat_id, topic_name)
            
        return topic_name
            
    def _process_text_frame(self, frame: TextFrame, metadata: dict) -> None:
        """Process a text frame."""
        topic_name = self._ensure_topic_exists(metadata)
        self.coordinator.save_message(topic_name, frame.content, metadata)

    def _process_image_frame(self, frame: ImageFrame, metadata: dict) -> None:
        """Process an image frame."""
        topic_name = self._ensure_topic_exists(metadata)
        
        # Save image attachment
        attachment_id = self.coordinator.save_attachment(
            topic_name,
            frame.content,
            'image',
            frame.format or 'unknown'
        )
        
        # Save message with attachment reference
        metadata['attachments'] = [{
            'id': attachment_id,
            'type': f'image/{frame.format or "unknown"}'
        }]
        self.coordinator.save_message(topic_name, frame.content or '', metadata)

    def _process_document_frame(self, frame: DocumentFrame, metadata: dict) -> None:
        """Process a document frame."""
        topic_name = self._ensure_topic_exists(metadata)
        
        # Save document attachment
        attachment_id = self.coordinator.save_attachment(
            topic_name,
            frame.content,
            'document',
            frame.mime_type,
            filename=frame.filename
        )
        
        # Save message with attachment reference and caption
        metadata['attachments'] = [{
            'id': attachment_id,
            'type': frame.mime_type,
            'filename': frame.filename
        }]
        metadata['content'] = frame.content
        self.coordinator.save_message(topic_name, frame.content or '', metadata)

    def _process_audio_frame(self, frame: AudioFrame, metadata: dict) -> None:
        """Process an audio frame."""
        topic_name = self._ensure_topic_exists(metadata)
        
        # Save audio attachment
        attachment_id = self.coordinator.save_attachment(
            topic_name,
            frame.content,
            'audio',
            frame.mime_type,
            duration=frame.duration
        )
        
        # Save message with attachment reference
        metadata['attachments'] = [{
            'id': attachment_id,
            'type': frame.mime_type,
            'duration': frame.duration
        }]
        self.coordinator.save_message(topic_name, frame.content or '', metadata)

    def _process_voice_frame(self, frame: VoiceFrame, metadata: dict) -> None:
        """Process a voice frame."""
        topic_name = self._ensure_topic_exists(metadata)
        
        # Save voice attachment
        attachment_id = self.coordinator.save_attachment(
            topic_name,
            frame.content,
            'voice',
            frame.mime_type,
            duration=frame.duration
        )
        
        # Save message with attachment reference
        metadata['attachments'] = [{
            'id': attachment_id,
            'type': frame.mime_type,
            'duration': frame.duration
        }]
        self.coordinator.save_message(topic_name, frame.content or '', metadata)

    def _process_sticker_frame(self, frame: StickerFrame, metadata: dict) -> None:
        """Process a sticker frame."""
        topic_name = self._ensure_topic_exists(metadata)
        
        # Save sticker attachment
        attachment_id = self.coordinator.save_attachment(
            topic_name,
            frame.content,
            'sticker',
            frame.format,
            emoji=frame.emoji,
            set_name=frame.set_name
        )
        
        # Save message with attachment reference
        metadata['attachments'] = [{
            'id': attachment_id,
            'type': f'image/{frame.format}',
            'emoji': frame.emoji,
            'set_name': frame.set_name
        }]
        self.coordinator.save_message(topic_name, frame.content or '', metadata)
            
    async def process_frame(self, frame: Frame) -> None:
        """Process a frame by saving it to storage."""
        try:
            logger.debug("Processing frame")
            metadata = frame.metadata

            # Validate metadata
            self._validate_metadata(metadata)

            # Ensure storage is initialized
            await self._ensure_initialized()

            # Process frame based on type
            if isinstance(frame, TextFrame):
                self._process_text_frame(frame, metadata)
            elif isinstance(frame, ImageFrame):
                self._process_image_frame(frame, metadata)
            elif isinstance(frame, DocumentFrame):
                self._process_document_frame(frame, metadata)
            elif isinstance(frame, AudioFrame):
                self._process_audio_frame(frame, metadata)
            elif isinstance(frame, VoiceFrame):
                self._process_voice_frame(frame, metadata)
            elif isinstance(frame, StickerFrame):
                self._process_sticker_frame(frame, metadata)
            else:
                logger.warning("Unsupported frame type")
                raise ProcessorValidationError(f"Unsupported frame type: {type(frame).__name__}")

        except (StorageError, ProcessorValidationError):
            # Re-raise storage and validation errors directly
            raise
        except Exception as e:
            logger.error(f"Failed to process frame: {str(e)}")
            raise StorageOperationError(str(e)) 