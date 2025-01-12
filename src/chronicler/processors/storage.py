"""Storage processor implementation."""
import logging
from typing import Optional
from datetime import datetime

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame, AudioFrame, VoiceFrame, StickerFrame
from chronicler.storage import StorageAdapter
from chronicler.storage.interface import Message, Attachment
from .base import BaseProcessor

logger = logging.getLogger(__name__)

class StorageProcessor(BaseProcessor):
    """Processor for storing frames in git."""
    
    def __init__(self, coordinator: StorageAdapter):
        """Initialize storage processor."""
        super().__init__()
        self.coordinator = coordinator
        logger.debug("PROC - Initialized StorageProcessor")
    
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame by storing its content."""
        try:
            if isinstance(frame, TextFrame):
                logger.debug("PROC - Processing text frame")
                message = Message(
                    content=frame.content,
                    source="telegram",
                    timestamp=datetime.utcnow(),
                    metadata=frame.metadata
                )
                await self.coordinator.save_message("default", message)
            
            elif isinstance(frame, ImageFrame):
                logger.debug("PROC - Processing image frame")
                if not frame.content:
                    raise ValueError("Image frame has no image data")
                
                message = Message(
                    content="[Image]",
                    source="telegram",
                    timestamp=datetime.utcnow(),
                    metadata=frame.metadata
                )
                message_id = await self.coordinator.save_message("default", message)
                attachment = Attachment(
                    id="image",
                    type="image",
                    filename=f"image.{frame.format}",
                    data=frame.content
                )
                await self.coordinator.save_attachment("default", message_id, attachment)
            
            elif isinstance(frame, DocumentFrame):
                logger.debug("PROC - Processing document frame")
                if not frame.content:
                    raise ValueError("Document frame has no content")
                
                message = Message(
                    content=frame.caption or "[Document]",
                    source="telegram",
                    timestamp=datetime.utcnow(),
                    metadata=frame.metadata
                )
                message_id = await self.coordinator.save_message("default", message)
                attachment = Attachment(
                    id="document",
                    type="document",
                    filename=frame.filename,
                    data=frame.content
                )
                await self.coordinator.save_attachment("default", message_id, attachment)
            
            elif isinstance(frame, AudioFrame):
                logger.debug("PROC - Processing audio frame")
                if not frame.content:
                    raise ValueError("Audio frame has no audio data")
                
                message = Message(
                    content=f"[Audio: {frame.duration}s]",
                    source="telegram",
                    timestamp=datetime.utcnow(),
                    metadata=frame.metadata
                )
                message_id = await self.coordinator.save_message("default", message)
                attachment = Attachment(
                    id="audio",
                    type="audio",
                    filename=f"audio.{frame.mime_type.split('/')[-1]}",
                    data=frame.content
                )
                await self.coordinator.save_attachment("default", message_id, attachment)
            
            elif isinstance(frame, VoiceFrame):
                logger.debug("PROC - Processing voice frame")
                if not frame.content:
                    raise ValueError("Voice frame has no audio data")
                
                message = Message(
                    content=f"[Voice: {frame.duration}s]",
                    source="telegram",
                    timestamp=datetime.utcnow(),
                    metadata=frame.metadata
                )
                message_id = await self.coordinator.save_message("default", message)
                attachment = Attachment(
                    id="voice",
                    type="voice",
                    filename=f"voice.{frame.mime_type.split('/')[-1]}",
                    data=frame.content
                )
                await self.coordinator.save_attachment("default", message_id, attachment)
            
            elif isinstance(frame, StickerFrame):
                logger.debug("PROC - Processing sticker frame")
                if not frame.content:
                    raise ValueError("Sticker frame has no sticker data")
                
                message = Message(
                    content=f"[Sticker: {frame.emoji}]",
                    source="telegram",
                    timestamp=datetime.utcnow(),
                    metadata=frame.metadata
                )
                message_id = await self.coordinator.save_message("default", message)
                attachment = Attachment(
                    id="sticker",
                    type="sticker",
                    filename=f"sticker_{frame.set_name}.webp",
                    data=frame.content
                )
                await self.coordinator.save_attachment("default", message_id, attachment)
            
            else:
                logger.warning(f"PROC - Unsupported frame type: {type(frame)}")
            
            return None
            
        except Exception as e:
            logger.error(f"PROC - Error processing frame: {e}")
            raise 