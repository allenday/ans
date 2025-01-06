"""Tests for storage processor."""
import pytest
from unittest.mock import Mock, AsyncMock, create_autospec
from datetime import datetime

from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame, AudioFrame, VoiceFrame, StickerFrame
from chronicler.processors.storage import StorageProcessor
from chronicler.storage import StorageAdapter
from chronicler.storage.interface import Message, Attachment

@pytest.fixture
def storage_mock():
    """Create a mock storage adapter."""
    storage = create_autospec(StorageAdapter)
    storage.init_storage.return_value = storage
    storage.create_topic.return_value = None
    storage.save_message = AsyncMock(return_value="msg_123")
    storage.save_attachment = AsyncMock(return_value=None)
    storage.sync = AsyncMock(return_value=None)
    storage.set_github_config = AsyncMock(return_value=None)
    storage.is_initialized.return_value = True
    return storage

@pytest.mark.asyncio
async def test_process_text_frame(storage_mock):
    """Test processing a text frame."""
    # Setup
    processor = StorageProcessor(storage_mock)
    frame = TextFrame(text="test message", metadata={"chat_id": 123})
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert result is None
    storage_mock.save_message.assert_called_once()
    call_args = storage_mock.save_message.call_args[0]
    assert call_args[0] == "default"
    message = call_args[1]
    assert isinstance(message, Message)
    assert message.content == "test message"
    assert message.source == "telegram"
    assert message.metadata == {"chat_id": 123}
    assert isinstance(message.timestamp, datetime)

@pytest.mark.asyncio
async def test_process_image_frame(storage_mock):
    """Test processing an image frame."""
    # Setup
    processor = StorageProcessor(storage_mock)
    frame = ImageFrame(image=b"test image", format="jpg", size=(100, 100), metadata={"chat_id": 123})
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert result is None
    storage_mock.save_message.assert_called_once()
    storage_mock.save_attachment.assert_called_once()
    
    message_call = storage_mock.save_message.call_args[0]
    assert message_call[0] == "default"
    message = message_call[1]
    assert isinstance(message, Message)
    assert message.content == "[Image]"
    assert message.source == "telegram"
    assert message.metadata == {"chat_id": 123}
    
    attachment_call = storage_mock.save_attachment.call_args[0]
    assert attachment_call[0] == "default"
    assert attachment_call[1] == "msg_123"
    attachment = attachment_call[2]
    assert isinstance(attachment, Attachment)
    assert attachment.id == "image"
    assert attachment.type == "image"
    assert attachment.filename == "image.jpg"
    assert attachment.data == b"test image"

@pytest.mark.asyncio
async def test_process_document_frame(storage_mock):
    """Test processing a document frame."""
    # Setup
    processor = StorageProcessor(storage_mock)
    frame = DocumentFrame(
        content=b"test doc",
        filename="test.txt",
        mime_type="text/plain",
        caption="Test document",
        metadata={"chat_id": 123}
    )
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert result is None
    storage_mock.save_message.assert_called_once()
    storage_mock.save_attachment.assert_called_once()
    
    message_call = storage_mock.save_message.call_args[0]
    assert message_call[0] == "default"
    message = message_call[1]
    assert isinstance(message, Message)
    assert message.content == "Test document"
    assert message.source == "telegram"
    assert message.metadata == {"chat_id": 123}
    
    attachment_call = storage_mock.save_attachment.call_args[0]
    assert attachment_call[0] == "default"
    assert attachment_call[1] == "msg_123"
    attachment = attachment_call[2]
    assert isinstance(attachment, Attachment)
    assert attachment.id == "document"
    assert attachment.type == "document"
    assert attachment.filename == "test.txt"
    assert attachment.data == b"test doc"

@pytest.mark.asyncio
async def test_process_audio_frame(storage_mock):
    """Test processing an audio frame."""
    # Setup
    processor = StorageProcessor(storage_mock)
    frame = AudioFrame(
        audio=b"test audio",
        duration=60,
        mime_type="audio/mp3",
        metadata={"chat_id": 123}
    )
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert result is None
    storage_mock.save_message.assert_called_once()
    storage_mock.save_attachment.assert_called_once()
    
    message_call = storage_mock.save_message.call_args[0]
    assert message_call[0] == "default"
    message = message_call[1]
    assert isinstance(message, Message)
    assert message.content == "[Audio: 60s]"
    assert message.source == "telegram"
    assert message.metadata == {"chat_id": 123}
    
    attachment_call = storage_mock.save_attachment.call_args[0]
    assert attachment_call[0] == "default"
    assert attachment_call[1] == "msg_123"
    attachment = attachment_call[2]
    assert isinstance(attachment, Attachment)
    assert attachment.id == "audio"
    assert attachment.type == "audio"
    assert attachment.filename == "audio.mp3"
    assert attachment.data == b"test audio"

@pytest.mark.asyncio
async def test_process_voice_frame(storage_mock):
    """Test processing a voice frame."""
    # Setup
    processor = StorageProcessor(storage_mock)
    frame = VoiceFrame(
        audio=b"test voice",
        duration=30,
        mime_type="audio/ogg",
        metadata={"chat_id": 123}
    )
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert result is None
    storage_mock.save_message.assert_called_once()
    storage_mock.save_attachment.assert_called_once()
    
    message_call = storage_mock.save_message.call_args[0]
    assert message_call[0] == "default"
    message = message_call[1]
    assert isinstance(message, Message)
    assert message.content == "[Voice: 30s]"
    assert message.source == "telegram"
    assert message.metadata == {"chat_id": 123}
    
    attachment_call = storage_mock.save_attachment.call_args[0]
    assert attachment_call[0] == "default"
    assert attachment_call[1] == "msg_123"
    attachment = attachment_call[2]
    assert isinstance(attachment, Attachment)
    assert attachment.id == "voice"
    assert attachment.type == "voice"
    assert attachment.filename == "voice.ogg"
    assert attachment.data == b"test voice"

@pytest.mark.asyncio
async def test_process_sticker_frame(storage_mock):
    """Test processing a sticker frame."""
    # Setup
    processor = StorageProcessor(storage_mock)
    frame = StickerFrame(
        sticker=b"test sticker",
        emoji="😀",
        set_name="test_set",
        metadata={"chat_id": 123}
    )
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert result is None
    storage_mock.save_message.assert_called_once()
    storage_mock.save_attachment.assert_called_once()
    
    message_call = storage_mock.save_message.call_args[0]
    assert message_call[0] == "default"
    message = message_call[1]
    assert isinstance(message, Message)
    assert message.content == "[Sticker: 😀]"
    assert message.source == "telegram"
    assert message.metadata == {"chat_id": 123}
    
    attachment_call = storage_mock.save_attachment.call_args[0]
    assert attachment_call[0] == "default"
    assert attachment_call[1] == "msg_123"
    attachment = attachment_call[2]
    assert isinstance(attachment, Attachment)
    assert attachment.id == "sticker"
    assert attachment.type == "sticker"
    assert attachment.filename == "sticker_test_set.webp"
    assert attachment.data == b"test sticker"

@pytest.mark.asyncio
async def test_process_unsupported_frame(storage_mock):
    """Test processing an unsupported frame type."""
    # Setup
    processor = StorageProcessor(storage_mock)
    frame = Mock()
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert result is None
    storage_mock.save_message.assert_not_called()
    storage_mock.save_attachment.assert_not_called() 