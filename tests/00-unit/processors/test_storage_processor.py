"""Tests for storage processor."""
import pytest
import os
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from git import Repo
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.processors.git_processor import GitProcessor
from chronicler.services.git_sync_service import GitSyncService
from chronicler.frames import TextFrame, ImageFrame, DocumentFrame

@pytest.fixture
def mock_storage_coordinator():
    """Mock storage coordinator."""
    coordinator = AsyncMock()
    coordinator.has_topic.return_value = False
    coordinator.init_storage.return_value = None
    coordinator.create_topic.return_value = None
    
    # Set up save_message to return a tuple
    coordinator.save_message.side_effect = lambda *args: ('message_path', ['media_path'])
    
    return coordinator

@pytest.fixture
def mock_git_processor():
    """Create a mock GitProcessor."""
    return Mock(spec=GitProcessor)

@pytest.fixture
def mock_git_sync_service():
    """Mock git sync service."""
    service = AsyncMock()
    future = asyncio.Future()
    future.set_result(None)
    service.start.return_value = future
    service.stop.return_value = future
    service.commit_immediately.return_value = future
    return service

@pytest.fixture
def temp_git_dir():
    """Create a temporary directory with a Git repository."""
    temp_dir = tempfile.mkdtemp()
    repo = Repo.init(temp_dir)
    # Create initial commit
    with open(os.path.join(temp_dir, "README.md"), "w") as f:
        f.write("# Test Repository")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def processor(mock_storage_coordinator, mock_git_sync_service, temp_git_dir):
    """Create a StorageProcessor with mocked dependencies."""
    with patch('chronicler.processors.storage_processor.StorageCoordinator', return_value=mock_storage_coordinator):
        processor = StorageProcessor(storage_path=temp_git_dir)
        processor.git_sync_service = mock_git_sync_service
        return processor

@pytest.mark.asyncio
async def test_start_processor(processor, mock_git_sync_service):
    """Test starting the storage processor."""
    await processor.start()
    assert mock_git_sync_service.start.called
    await mock_git_sync_service.start.return_value

@pytest.mark.asyncio
async def test_stop_processor(processor, mock_git_sync_service):
    """Test stopping the storage processor."""
    await processor.stop()
    assert mock_git_sync_service.stop.called
    await mock_git_sync_service.stop.return_value

@pytest.mark.asyncio
async def test_process_text_frame(processor, mock_storage_coordinator, mock_git_sync_service):
    """Test processing a text frame."""
    # Set up futures for async methods
    has_topic_future = asyncio.Future()
    has_topic_future.set_result(False)
    mock_storage_coordinator.has_topic.return_value = has_topic_future
    
    save_message_future = asyncio.Future()
    save_message_future.set_result(('message_path', ['media_path']))
    mock_storage_coordinator.save_message.return_value = save_message_future
    
    frame = TextFrame(content="Test message")
    frame.metadata = {"thread_id": 1, "chat_id": 123}

    await processor.process_frame(frame)

    # Verify the mock was called
    assert mock_storage_coordinator.has_topic.called
    assert mock_storage_coordinator.save_message.called
    assert mock_git_sync_service.commit_immediately.called

@pytest.mark.asyncio
async def test_process_image_frame(processor, mock_storage_coordinator, mock_git_sync_service):
    """Test processing an image frame."""
    frame = ImageFrame(content=b"test image", size=(100, 100), format="jpg")
    frame.metadata = {"thread_id": 1, "chat_id": 123}

    await processor.process_frame(frame)

    assert mock_storage_coordinator.save_message.called
    assert mock_git_sync_service.commit_immediately.called
    await mock_git_sync_service.commit_immediately.return_value

@pytest.mark.asyncio
async def test_git_commit_failure_doesnt_break_processing(processor, mock_storage_coordinator, mock_git_sync_service):
    """Test that git commit failures don't break message processing."""
    frame = TextFrame(content="Test message")
    frame.metadata = {"thread_id": 1, "chat_id": 123}
    
    mock_git_sync_service.commit_immediately.side_effect = Exception("Git error")
    
    await processor.process_frame(frame)
    
    assert mock_storage_coordinator.has_topic.called
    assert mock_storage_coordinator.save_message.called

@pytest.mark.asyncio
async def test_no_git_sync_service(mock_storage_coordinator, temp_git_dir):
    """Test processor works without git sync service."""
    with patch('chronicler.processors.storage_processor.StorageCoordinator', return_value=mock_storage_coordinator):
        processor = StorageProcessor(storage_path=temp_git_dir)
        processor.git_sync_service = None
        
        frame = TextFrame(content="Test message", metadata={'thread_id': 1, 'chat_id': 123})
        await processor.process_frame(frame)
        
        assert mock_storage_coordinator.save_message.called 