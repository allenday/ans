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
            content="test message",
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

        # Verify error is raised
        with pytest.raises(ValueError, match="Unsupported frame type: UnsupportedFrame"):
            await processor.process_frame(frame)
        
        # Verify no topic was created
        storage_mock.create_topic.assert_not_called()
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
            content="test message",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        )
        
        # Execute and verify error is propagated
        with pytest.raises(RuntimeError, match="Test error"):
            await processor.process_frame(frame) 

@pytest.mark.asyncio
async def test_process_frame_missing_thread_id(storage_mock):
    """Test processing a frame with missing thread_id."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = TextFrame(
            content="test message",
            metadata={
                "chat_id": 123,  # Missing thread_id
                "chat_title": "Test Chat"
            }
        )
        
        # Verify error is raised
        with pytest.raises(ValueError, match="Message metadata must include thread_id"):
            await processor.process_frame(frame)
        
        # Verify no topic was created
        storage_mock.create_topic.assert_not_called()
        storage_mock.save_message.assert_not_called()

@pytest.mark.asyncio
async def test_process_frame_missing_chat_id(storage_mock):
    """Test processing a frame with missing chat_id."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = TextFrame(
            content="test message",
            metadata={
                "thread_id": 456,  # Missing chat_id
                "chat_title": "Test Chat"
            }
        )
        
        # Verify error is raised
        with pytest.raises(ValueError, match="Message metadata must include chat_id"):
            await processor.process_frame(frame)
        
        # Verify no topic was created
        storage_mock.create_topic.assert_not_called()
        storage_mock.save_message.assert_not_called()

@pytest.mark.asyncio
async def test_process_frame_invalid_metadata_type(storage_mock):
    """Test processing a frame with invalid metadata type."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = TextFrame(
            content="test message",
            metadata={
                "chat_id": "invalid",  # Should be integer
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        )
        
        # Verify error is raised
        with pytest.raises(TypeError, match="chat_id must be an integer"):
            await processor.process_frame(frame)
        
        # Verify no topic was created
        storage_mock.create_topic.assert_not_called()
        storage_mock.save_message.assert_not_called()

@pytest.mark.asyncio
async def test_process_frame_metadata_propagation(storage_mock):
    """Test metadata is correctly propagated to topic and message."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        test_metadata = {
            "chat_id": 123,
            "thread_id": 456,
            "chat_title": "Test Chat",
            "message_id": 789,
            "from_user": "test_user",
            "custom_field": "custom_value"
        }
        
        frame = TextFrame(
            content="test message",
            metadata=test_metadata
        )
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify topic creation with metadata
        storage_mock.create_topic.assert_called_once()
        topic_call = storage_mock.create_topic.call_args[0][0]
        assert isinstance(topic_call, Topic)
        assert topic_call.metadata["chat_id"] == 123
        assert topic_call.metadata["thread_id"] == 456
        assert topic_call.metadata["source"] == "telegram"
        
        # Verify message creation with metadata
        storage_mock.save_message.assert_called_once()
        message_call = storage_mock.save_message.call_args[0][1]
        assert isinstance(message_call, Message)
        assert message_call.metadata["chat_id"] == 123
        assert message_call.metadata["thread_id"] == 456
        assert message_call.metadata["message_id"] == 789
        assert message_call.metadata["from_user"] == "test_user"
        assert message_call.metadata["custom_field"] == "custom_value"
        assert message_call.metadata["source"] == "telegram" 

@pytest.mark.asyncio
async def test_create_topic_duplicate(storage_mock):
    """Test handling of duplicate topic creation."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        # Make create_topic raise ValueError on second call
        storage_mock.create_topic.side_effect = [
            "test_topic",  # First call succeeds
            ValueError("Topic already exists")  # Second call fails
        ]
        
        # First frame - should succeed
        frame1 = TextFrame(
            content="first message",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        )
        await processor.process_frame(frame1)
        
        # Second frame with same topic - should handle error
        frame2 = TextFrame(
            content="second message",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        )
        await processor.process_frame(frame2)
        
        # Verify topic was only created once
        assert storage_mock.create_topic.call_count == 2
        assert storage_mock.save_message.call_count == 2

@pytest.mark.asyncio
async def test_create_topic_invalid_name(storage_mock):
    """Test handling of invalid topic names."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        # Make create_topic raise ValueError for invalid name
        storage_mock.create_topic.side_effect = ValueError("Invalid topic name")
        
        frame = TextFrame(
            content="test message",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Invalid/Name/With/Slashes"
            }
        )
        
        # Verify error is propagated
        with pytest.raises(ValueError, match="Invalid topic name"):
            await processor.process_frame(frame)
        
        # Verify no message was saved
        storage_mock.save_message.assert_not_called()

@pytest.mark.asyncio
async def test_create_topic_missing_chat_title(storage_mock):
    """Test handling of missing chat title in metadata."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = TextFrame(
            content="test message",
            metadata={
                "chat_id": 123,
                "thread_id": 456
                # Missing chat_title
            }
        )
        
        # Execute - should use default name
        await processor.process_frame(frame)
        
        # Verify topic creation with default name
        storage_mock.create_topic.assert_called_once()
        topic_call = storage_mock.create_topic.call_args[0][0]
        assert isinstance(topic_call, Topic)
        assert topic_call.name == "Unknown"  # Default name
        assert topic_call.metadata["chat_id"] == 123
        assert topic_call.metadata["thread_id"] == 456

@pytest.mark.asyncio
async def test_create_topic_metadata_validation(storage_mock):
    """Test validation of topic metadata during creation."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = TextFrame(
            content="test message",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat",
                "custom_field": "custom_value"
            }
        )
        
        # Execute
        await processor.process_frame(frame)
        
        # Verify topic metadata
        storage_mock.create_topic.assert_called_once()
        topic_call = storage_mock.create_topic.call_args[0][0]
        assert isinstance(topic_call, Topic)
        assert topic_call.metadata["chat_id"] == 123
        assert topic_call.metadata["thread_id"] == 456
        assert topic_call.metadata["source"] == "telegram"
        assert "custom_field" not in topic_call.metadata  # Custom fields should not be included

@pytest.mark.asyncio
async def test_frame_content_validation_empty_text(storage_mock):
    """Test validation of empty text content."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = TextFrame(
            content="",  # Empty text
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        )
        
        # Execute - should still process empty text
        await processor.process_frame(frame)
        
        # Verify message was saved with empty content
        storage_mock.save_message.assert_called_once()
        message_call = storage_mock.save_message.call_args[0][1]
        assert isinstance(message_call, Message)
        assert message_call.content == ""

@pytest.mark.asyncio
async def test_frame_content_validation_empty_image(storage_mock):
    """Test validation of empty image content."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = ImageFrame(
            content=b"",  # Empty image data
            size=(0, 0),
            format="jpeg",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat",
                "file_id": "test_file_id"
            }
        )
        
        # Execute - should raise error for empty image
        with pytest.raises(ValueError, match="Image content cannot be empty"):
            await processor.process_frame(frame)
        
        # Verify no message was saved
        storage_mock.save_message.assert_not_called()

@pytest.mark.asyncio
async def test_frame_processing_error_save_message(storage_mock):
    """Test error handling when save_message fails."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        # Make save_message raise an error
        storage_mock.save_message.side_effect = RuntimeError("Failed to save message")
        
        frame = TextFrame(
            content="test message",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat"
            }
        )
        
        # Verify error is propagated
        with pytest.raises(RuntimeError, match="Failed to save message"):
            await processor.process_frame(frame)

@pytest.mark.asyncio
async def test_frame_processing_error_invalid_mime_type(storage_mock):
    """Test error handling for invalid MIME type."""
    # Setup
    with patch('chronicler.processors.storage_processor.StorageCoordinator') as mock_coordinator:
        mock_coordinator.return_value = storage_mock
        processor = StorageProcessor(Path("/test/path"))
        processor._initialized = True
        
        frame = DocumentFrame(
            content=b"test content",
            filename="test.xyz",
            mime_type="invalid/type",  # Invalid MIME type
            caption="Test document",
            metadata={
                "chat_id": 123,
                "thread_id": 456,
                "chat_title": "Test Chat",
                "file_id": "test_file_id"
            }
        )
        
        # Execute - should raise error for invalid MIME type
        with pytest.raises(ValueError, match="Invalid MIME type: invalid/type"):
            await processor.process_frame(frame)
        
        # Verify no message was saved
        storage_mock.save_message.assert_not_called()
 