"""Unit tests for storage processor implementation."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from chronicler.frames.media import (
    TextFrame, ImageFrame, DocumentFrame, 
    AudioFrame, VoiceFrame, StickerFrame
)
from chronicler.frames.base import Frame
from chronicler.exceptions import (
    StorageError, StorageInitializationError, 
    StorageOperationError, StorageValidationError,
    ProcessorValidationError
)
from chronicler.processors.storage_processor import StorageProcessor
from tests.mocks.processors import storage_processor, storage, metadata

def test_storage_processor_init(storage):
    """Test storage processor initialization."""
    processor = StorageProcessor(storage)
    assert processor.coordinator == storage
    assert not processor._initialized

def test_storage_processor_stop(storage_processor):
    """Test stopping the storage processor."""
    storage_processor.stop()
    assert not storage_processor._initialized
    storage_processor.coordinator.stop.assert_called_once()

@pytest.mark.asyncio
async def test_process_returns_none(storage_processor, metadata):
    """Test that process always returns None."""
    frame = TextFrame(content="test", metadata=metadata)
    result = await storage_processor.process(frame)
    assert result is None

@pytest.mark.asyncio
async def test_ensure_initialized(storage_processor):
    """Test storage initialization."""
    await storage_processor._ensure_initialized()
    assert storage_processor._initialized

def test_validate_metadata_missing_field(storage_processor):
    """Test metadata validation with missing field."""
    with pytest.raises(StorageValidationError, match="must include thread_id"):
        storage_processor._validate_metadata({'chat_id': 123})

def test_ensure_topic_exists_new(storage_processor, metadata):
    """Test ensuring topic exists when it doesn't."""
    topic_name = storage_processor._ensure_topic_exists(metadata)
    assert topic_name == "123:456"
    storage_processor.coordinator.create_topic.assert_called_once_with(123, "123:456")

def test_ensure_topic_exists_existing(storage_processor, metadata):
    """Test ensuring topic exists when it does."""
    storage_processor.coordinator.topic_exists.return_value = True
    topic_name = storage_processor._ensure_topic_exists(metadata)
    assert topic_name == "123:456"
    storage_processor.coordinator.create_topic.assert_not_called()

def test_process_text_frame(storage_processor, metadata):
    """Test processing a text frame."""
    frame = TextFrame(content="test message", metadata=metadata)
    storage_processor._process_text_frame(frame, metadata)
    storage_processor.coordinator.save_message.assert_called_once_with(
        "123:456", "test message", metadata
    )

def test_process_image_frame(storage_processor, metadata):
    """Test processing an image frame."""
    frame = ImageFrame(
        content=b"image data",
        format="jpeg",
        metadata=metadata
    )
    storage_processor.coordinator.save_attachment.return_value = "att123"
    
    storage_processor._process_image_frame(frame, metadata)
    
    storage_processor.coordinator.save_attachment.assert_called_once_with(
        "123:456", b"image data", "image", "jpeg"
    )
    assert metadata["attachments"][0]["id"] == "att123"
    assert metadata["attachments"][0]["type"] == "image/jpeg"

def test_process_document_frame(storage_processor, metadata):
    """Test processing a document frame."""
    frame = DocumentFrame(
        content=b"document data",
        filename="test.pdf",
        mime_type="application/pdf",
        metadata=metadata
    )
    storage_processor.coordinator.save_attachment.return_value = "att123"
    
    storage_processor._process_document_frame(frame, metadata)
    
    storage_processor.coordinator.save_attachment.assert_called_once_with(
        "123:456", b"document data", "document", "application/pdf",
        filename="test.pdf"
    )
    assert metadata["attachments"][0]["id"] == "att123"
    assert metadata["attachments"][0]["type"] == "application/pdf"
    assert metadata["attachments"][0]["filename"] == "test.pdf"

def test_process_audio_frame(storage_processor, metadata):
    """Test processing an audio frame."""
    frame = AudioFrame(
        content=b"audio data",
        mime_type="audio/mp3",
        duration=120,
        metadata=metadata
    )
    storage_processor.coordinator.save_attachment.return_value = "att123"
    
    storage_processor._process_audio_frame(frame, metadata)
    
    storage_processor.coordinator.save_attachment.assert_called_once_with(
        "123:456", b"audio data", "audio", "audio/mp3",
        duration=120
    )
    assert metadata["attachments"][0]["id"] == "att123"
    assert metadata["attachments"][0]["type"] == "audio/mp3"
    assert metadata["attachments"][0]["duration"] == 120

def test_process_voice_frame(storage_processor, metadata):
    """Test processing a voice frame."""
    frame = VoiceFrame(
        content=b"voice data",
        mime_type="audio/ogg",
        duration=30,
        metadata=metadata
    )
    storage_processor.coordinator.save_attachment.return_value = "att123"
    
    storage_processor._process_voice_frame(frame, metadata)
    
    storage_processor.coordinator.save_attachment.assert_called_once_with(
        "123:456", b"voice data", "voice", "audio/ogg",
        duration=30
    )
    assert metadata["attachments"][0]["id"] == "att123"
    assert metadata["attachments"][0]["type"] == "audio/ogg"
    assert metadata["attachments"][0]["duration"] == 30

def test_process_sticker_frame(storage_processor, metadata):
    """Test processing a sticker frame."""
    frame = StickerFrame(
        content=b"sticker data",
        format="webp",
        emoji="😀",
        set_name="test_set",
        metadata=metadata
    )
    storage_processor.coordinator.save_attachment.return_value = "att123"
    
    storage_processor._process_sticker_frame(frame, metadata)
    
    storage_processor.coordinator.save_attachment.assert_called_once_with(
        "123:456", b"sticker data", "sticker", "webp",
        emoji="😀", set_name="test_set"
    )
    assert metadata["attachments"][0]["id"] == "att123"
    assert metadata["attachments"][0]["type"] == "image/webp"
    assert metadata["attachments"][0]["emoji"] == "😀"
    assert metadata["attachments"][0]["set_name"] == "test_set"

@pytest.mark.asyncio
async def test_process_frame_unsupported_type(storage_processor, metadata):
    """Test processing an unsupported frame type."""
    class UnsupportedFrame(Frame):
        pass

    frame = UnsupportedFrame(content="test", metadata=metadata)
    with pytest.raises(ProcessorValidationError, match="Unsupported frame type: UnsupportedFrame"):
        await storage_processor.process(frame)

@pytest.mark.asyncio
async def test_process_frame_missing_metadata(storage_processor):
    """Test processing a frame without metadata."""
    frame = TextFrame(content="test", metadata={})
    with pytest.raises(StorageValidationError, match="Message metadata must include chat_id"):
        await storage_processor.process(frame)

@pytest.mark.asyncio
async def test_process_frame_initialization_error(storage_processor, metadata):
    """Test processing a frame when storage is not initialized."""
    frame = TextFrame(content="test", metadata=metadata)
    storage_processor._initialized = False
    storage_processor.coordinator.init_storage = AsyncMock(side_effect=StorageInitializationError("Init failed"))
    with pytest.raises(StorageInitializationError, match="Init failed"):
        await storage_processor.process(frame)

@pytest.mark.asyncio
async def test_process_frame_save_error(storage_processor, metadata):
    """Test processing a frame when save fails."""
    frame = TextFrame(content="test", metadata=metadata)
    storage_processor.coordinator.save_message.side_effect = StorageOperationError("Save failed")
    with pytest.raises(StorageOperationError, match="Save failed"):
        await storage_processor.process_frame(frame)

def test_ensure_topic_exists(storage_processor, metadata):
    """Test ensuring a topic exists."""
    topic_name = storage_processor._ensure_topic_exists(metadata)
    storage_processor.coordinator.create_topic.assert_called_once_with(metadata["chat_id"], topic_name) 