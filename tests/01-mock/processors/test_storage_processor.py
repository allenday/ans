"""Mock tests for StorageProcessor."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from chronicler.pipeline import TextFrame, DocumentFrame
from chronicler.processors.storage_processor import StorageProcessor

@pytest.fixture
def storage_path(tmp_path):
    """Create a temporary storage path."""
    return tmp_path / "test_storage"

@pytest.fixture
async def processor(storage_path):
    """Create a StorageProcessor instance."""
    return StorageProcessor(storage_path)

@pytest.mark.asyncio
async def test_text_frame_processing(processor):
    """Test processing a text frame."""
    frame = TextFrame(
        text="test message",
        metadata={
            'chat_id': 123,
            'chat_title': "Test Chat",
            'thread_id': 1,
            'thread_name': "Test Topic"
        }
    )
    
    # Mock storage methods
    processor.storage.init_storage = AsyncMock()
    processor.storage.create_topic = AsyncMock()
    processor.storage.save_message = AsyncMock()
    
    await processor.process_frame(frame)
    
    # Verify storage was initialized
    processor.storage.init_storage.assert_called_once()
    # Verify topic was created
    processor.storage.create_topic.assert_called_once()
    # Verify message was saved
    processor.storage.save_message.assert_called_once()

@pytest.mark.asyncio
async def test_document_frame_processing(processor):
    """Test processing a document frame."""
    frame = DocumentFrame(
        content=b"test content",
        filename="test.txt",
        mime_type="text/plain",
        metadata={
            'chat_id': 123,
            'chat_title': "Test Chat",
            'thread_id': 1,
            'thread_name': "Test Topic"
        }
    )
    
    # Mock storage methods
    processor.storage.init_storage = AsyncMock()
    processor.storage.create_topic = AsyncMock()
    processor.storage.save_message = AsyncMock()
    
    await processor.process_frame(frame)
    
    # Verify storage was initialized
    processor.storage.init_storage.assert_called_once()
    # Verify topic was created
    processor.storage.create_topic.assert_called_once()
    # Verify message was saved
    processor.storage.save_message.assert_called_once() 