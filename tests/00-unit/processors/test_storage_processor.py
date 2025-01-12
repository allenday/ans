"""Tests for storage processor."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from pathlib import Path

from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame, AudioFrame, VoiceFrame, StickerFrame
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.storage.interface import Message, Attachment, User, Topic

@pytest.fixture
def storage_mock():
    """Create a mock storage coordinator."""
    mock = AsyncMock()
    mock.init_storage = AsyncMock()
    mock.create_topic = AsyncMock(return_value="test_topic")
    mock.save_message = AsyncMock(return_value="test_message")
    return mock

@pytest.mark.asyncio
async def test_initialization(storage_mock):
    """Test storage processor initialization."""
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        storage_path = Path("/test/path")
        processor = StorageProcessor(storage_path)
        assert not processor._initialized
        
        # Test initialization
        await processor._ensure_initialized()
        assert processor._initialized
        processor.storage.init_storage.assert_called_once()
        
        # Test subsequent calls don't reinitialize
        await processor._ensure_initialized()
        assert processor.storage.init_storage.call_count == 1

@pytest.mark.asyncio
async def test_process_text_frame(storage_mock):
    """Test processing a text frame."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = TextFrame(
            text="test message",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        )
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify topic creation
        storage_mock.create_topic.assert_called_once()
        topic_call = storage_mock.create_topic.call_args[0][0]
        assert isinstance(topic_call, Topic)
        assert topic_call.name == "Test Chat"
        assert topic_call.metadata["chat_id"] == 123
        assert topic_call.metadata["thread_id"] == 456
        
        # Verify message saving
        storage_mock.save_message.assert_called_once()
        message_call = storage_mock.save_message.call_args[0]
        assert message_call[0] == "test_topic"  # topic_id from mock
        message = message_call[1]
        assert isinstance(message, Message)
        assert message.content == "test message"
        assert message.source == "telegram"
        assert message.metadata["chat_id"] == 123

@pytest.mark.asyncio
async def test_process_image_frame(storage_mock):
    """Test processing an image frame."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = ImageFrame(
            content=b"test image",
            size=(100, 100),
            format="jpeg",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat",
                "file_id": "test_file_id"
            }
        )
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify topic creation
        storage_mock.create_topic.assert_called_once()
        topic_call = storage_mock.create_topic.call_args[0][0]
        assert isinstance(topic_call, Topic)
        assert topic_call.name == "Test Chat"
        
        # Verify message saving
        storage_mock.save_message.assert_called_once()
        message_call = storage_mock.save_message.call_args[0]
        assert message_call[0] == "test_topic"
        message = message_call[1]
        assert isinstance(message, Message)
        assert message.content == ""  # Empty content for images
        assert message.source == "telegram"
        assert len(message.attachments) == 1
        
        # Verify attachment
        attachment = message.attachments[0]
        assert attachment.id == "test_file_id"
        assert attachment.type == "image/jpeg"
        assert attachment.filename == "test_file_id.jpeg"
        assert attachment.data == frame.content

@pytest.mark.asyncio
async def test_process_document_frame(storage_mock):
    """Test processing a document frame."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = DocumentFrame(
            content=b"test doc",
            filename="test.txt",
            mime_type="text/plain",
            caption="Test document",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat",
                "file_id": "test_file_id"
            }
        )
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify message saving
        storage_mock.save_message.assert_called_once()
        message_call = storage_mock.save_message.call_args[0]
        assert message_call[0] == "test_topic"
        message = message_call[1]
        assert isinstance(message, Message)
        assert message.content == "Test document"
        assert message.source == "telegram"
        assert len(message.attachments) == 1
        
        # Verify attachment
        attachment = message.attachments[0]
        assert attachment.id == "test_file_id"
        assert attachment.type == "text/plain"
        assert attachment.filename == "test.txt"
        assert attachment.data == frame.content

@pytest.mark.asyncio
async def test_process_audio_frame(storage_mock):
    """Test processing an audio frame."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = AudioFrame(
            content=b"test audio",
            duration=60,
            mime_type="audio/mp3",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat",
                "file_id": "test_file_id"
            }
        )
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify message saving
        storage_mock.save_message.assert_called_once()
        message_call = storage_mock.save_message.call_args[0]
        assert message_call[0] == "test_topic"
        message = message_call[1]
        assert isinstance(message, Message)
        assert message.content == ""
        assert message.source == "telegram"
        assert len(message.attachments) == 1
        
        # Verify attachment
        attachment = message.attachments[0]
        assert attachment.id == "test_file_id"
        assert attachment.type == "audio/mp3"
        assert attachment.filename == "test_file_id.mp3"
        assert attachment.data == frame.content

@pytest.mark.asyncio
async def test_process_voice_frame(storage_mock):
    """Test processing a voice frame."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = VoiceFrame(
            content=b"test voice",
            duration=30,
            mime_type="audio/ogg",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat",
                "file_id": "test_file_id"
            }
        )
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify message saving
        storage_mock.save_message.assert_called_once()
        message_call = storage_mock.save_message.call_args[0]
        assert message_call[0] == "test_topic"
        message = message_call[1]
        assert isinstance(message, Message)
        assert message.content == ""
        assert message.source == "telegram"
        assert len(message.attachments) == 1
        
        # Verify attachment
        attachment = message.attachments[0]
        assert attachment.id == "test_file_id"
        assert attachment.type == "audio/ogg"
        assert attachment.filename == "test_file_id.ogg"
        assert attachment.data == frame.content

@pytest.mark.asyncio
async def test_process_sticker_frame(storage_mock):
    """Test processing a sticker frame."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = StickerFrame(
            content=b"test sticker",
            emoji="😀",
            set_name="test_set",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat",
                "file_id": "test_file_id"
            }
        )
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify message saving
        storage_mock.save_message.assert_called_once()
        message_call = storage_mock.save_message.call_args[0]
        assert message_call[0] == "test_topic"
        message = message_call[1]
        assert isinstance(message, Message)
        assert message.content == ""
        assert message.source == "telegram"
        assert len(message.attachments) == 1
        
        # Verify attachment
        attachment = message.attachments[0]
        assert attachment.id == "test_file_id"
        assert attachment.type == "image/webp"
        assert attachment.filename == "test_file_id.webp"
        assert attachment.data == frame.content

@pytest.mark.asyncio
async def test_process_unsupported_frame(storage_mock):
    """Test processing an unsupported frame type."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        class UnsupportedFrame:
            metadata = {
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        
        frame = UnsupportedFrame()
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify topic was still created
        storage_mock.create_topic.assert_called_once()
        
        # Verify no message was saved
        storage_mock.save_message.assert_not_called()

@pytest.mark.asyncio
async def test_error_handling(storage_mock):
    """Test error handling during frame processing."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        # Make storage.save_message raise an error
        storage_mock.save_message.side_effect = RuntimeError("Test error")
        
        frame = TextFrame(
            text="test message",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        )
        
        # Execute and verify error is propagated
        with pytest.raises(RuntimeError, match="Test error"):
            await processor.process_frame(frame) 