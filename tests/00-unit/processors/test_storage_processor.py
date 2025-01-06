"""Unit tests for StorageProcessor."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from pathlib import Path

from chronicler.pipeline import (
    TextFrame, ImageFrame, DocumentFrame,
    AudioFrame, VoiceFrame, StickerFrame
)
from chronicler.processors import StorageProcessor
from chronicler.storage import Message, Attachment

@pytest.fixture
def mock_storage():
    """Create a mock storage instance."""
    storage = AsyncMock()
    storage.save_message = AsyncMock()
    return storage

@pytest.fixture
def storage_processor(mock_storage):
    """Create a StorageProcessor instance with mock storage."""
    with patch('chronicler.processors.storage_processor.StorageCoordinator', return_value=mock_storage):
        processor = StorageProcessor(storage_path=Path('/tmp/test'))
        return processor

@pytest.mark.asyncio
async def test_process_text_frame(storage_processor, mock_storage):
    """Test processing a text frame."""
    frame = TextFrame(text="test message", metadata={'key': 'value'})
    topic_id = "test_topic"
    
    await storage_processor._process_text_frame(topic_id, frame, frame.metadata)
    
    mock_storage.save_message.assert_called_once()
    call_args = mock_storage.save_message.call_args[0]
    assert call_args[0] == topic_id
    message = call_args[1]
    assert isinstance(message, Message)
    assert message.content == "test message"
    assert message.metadata == {'key': 'value'}

@pytest.mark.asyncio
async def test_process_image_frame(storage_processor, mock_storage):
    """Test processing an image frame."""
    frame = ImageFrame(
        image=b"test_image_data",
        size=(100, 200),
        format="jpeg",
        metadata={'file_id': 'test123'}
    )
    topic_id = "test_topic"
    
    await storage_processor._process_image_frame(topic_id, frame, frame.metadata)
    
    mock_storage.save_message.assert_called_once()
    call_args = mock_storage.save_message.call_args[0]
    assert call_args[0] == topic_id
    message = call_args[1]
    assert isinstance(message, Message)
    assert message.content == ''  # Empty content for images
    assert message.metadata == {'file_id': 'test123'}
    assert len(message.attachments) == 1
    attachment = message.attachments[0]
    assert attachment.type == "image/jpeg"
    assert attachment.data == b"test_image_data"
    assert attachment.id == "test123"

@pytest.mark.asyncio
async def test_process_document_frame(storage_processor, mock_storage):
    """Test processing a document frame."""
    frame = DocumentFrame(
        content=b"test_document_data",
        filename="test.txt",
        mime_type="text/plain",
        caption="Test Caption",
        metadata={'file_id': 'test123'}
    )
    topic_id = "test_topic"
    
    await storage_processor._process_document_frame(topic_id, frame, frame.metadata)
    
    mock_storage.save_message.assert_called_once()
    call_args = mock_storage.save_message.call_args[0]
    assert call_args[0] == topic_id
    message = call_args[1]
    assert isinstance(message, Message)
    assert message.content == "Test Caption"
    assert message.metadata == {'file_id': 'test123'}
    assert len(message.attachments) == 1
    attachment = message.attachments[0]
    assert attachment.type == "text/plain"
    assert attachment.data == b"test_document_data"
    assert attachment.id == "test123"
    assert attachment.filename == "test.txt"

@pytest.mark.asyncio
async def test_process_audio_frame(storage_processor, mock_storage):
    """Test processing an audio frame."""
    frame = AudioFrame(
        audio=b"test_audio_data",
        duration=120,
        mime_type="audio/mp3",
        metadata={'file_id': 'test123'}
    )
    topic_id = "test_topic"
    
    await storage_processor._process_audio_frame(topic_id, frame, frame.metadata)
    
    mock_storage.save_message.assert_called_once()
    call_args = mock_storage.save_message.call_args[0]
    assert call_args[0] == topic_id
    message = call_args[1]
    assert isinstance(message, Message)
    assert message.content == ''  # Empty content for audio
    assert message.metadata == {'file_id': 'test123', 'duration': 120}
    assert len(message.attachments) == 1
    attachment = message.attachments[0]
    assert attachment.type == "audio/mp3"
    assert attachment.data == b"test_audio_data"
    assert attachment.id == "test123"

@pytest.mark.asyncio
async def test_process_voice_frame(storage_processor, mock_storage):
    """Test processing a voice frame."""
    frame = VoiceFrame(
        audio=b"test_voice_data",
        duration=30,
        mime_type="audio/ogg",
        metadata={'file_id': 'test123'}
    )
    topic_id = "test_topic"
    
    await storage_processor._process_voice_frame(topic_id, frame, frame.metadata)
    
    mock_storage.save_message.assert_called_once()
    call_args = mock_storage.save_message.call_args[0]
    assert call_args[0] == topic_id
    message = call_args[1]
    assert isinstance(message, Message)
    assert message.content == ''  # Empty content for voice
    assert message.metadata == {'file_id': 'test123', 'duration': 30}
    assert len(message.attachments) == 1
    attachment = message.attachments[0]
    assert attachment.type == "audio/ogg"
    assert attachment.data == b"test_voice_data"
    assert attachment.id == "test123"

@pytest.mark.asyncio
async def test_process_sticker_frame(storage_processor, mock_storage):
    """Test processing a sticker frame."""
    frame = StickerFrame(
        sticker=b"test_sticker_data",
        emoji="😀",
        set_name="TestSet",
        metadata={'file_id': 'test123'}
    )
    topic_id = "test_topic"
    
    await storage_processor._process_sticker_frame(topic_id, frame, frame.metadata)
    
    mock_storage.save_message.assert_called_once()
    call_args = mock_storage.save_message.call_args[0]
    assert call_args[0] == topic_id
    message = call_args[1]
    assert isinstance(message, Message)
    assert message.content == '😀'  # Emoji as content
    assert message.metadata == {
        'file_id': 'test123',
        'emoji': '😀',
        'set_name': 'TestSet'
    }
    assert len(message.attachments) == 1
    attachment = message.attachments[0]
    assert attachment.type == "image/webp"  # Stickers are typically WebP
    assert attachment.data == b"test_sticker_data"
    assert attachment.id == "test123"

@pytest.mark.asyncio
async def test_process_frame_with_missing_file_id(storage_processor, mock_storage):
    """Test processing frames without file_id in metadata."""
    frames = [
        ImageFrame(image=b"data", size=(100,100), format="jpeg", metadata={'chat_id': '123', 'thread_id': '456'}),
        DocumentFrame(content=b"data", filename="test.txt", mime_type="text/plain", metadata={'chat_id': '123', 'thread_id': '456'}),
        AudioFrame(audio=b"data", duration=120, mime_type="audio/mp3", metadata={'chat_id': '123', 'thread_id': '456'}),
        VoiceFrame(audio=b"data", duration=30, mime_type="audio/ogg", metadata={'chat_id': '123', 'thread_id': '456'}),
        StickerFrame(sticker=b"data", emoji="😀", set_name="TestSet", metadata={'chat_id': '123', 'thread_id': '456'})
    ]
    
    prefixes = {
        ImageFrame: "image_",
        DocumentFrame: "unknown",
        AudioFrame: "audio_",
        VoiceFrame: "voice_",
        StickerFrame: "sticker_"
    }
    
    for frame in frames:
        await storage_processor.process_frame(frame)
        
        call_args = mock_storage.save_message.call_args[0]
        message = call_args[1]
        assert len(message.attachments) == 1
        attachment = message.attachments[0]
        # Should generate a timestamp-based ID with appropriate prefix
        assert attachment.id.startswith(prefixes[frame.__class__]) 