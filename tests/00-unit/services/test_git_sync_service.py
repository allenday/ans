import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from chronicler.processors.git_processor import GitProcessor, GitProcessingError
from chronicler.services.git_sync_service import GitSyncService

@pytest.fixture
def mock_git_processor():
    """Create a mock GitProcessor."""
    return Mock(spec=GitProcessor)

@pytest.fixture
def git_sync_service(mock_git_processor):
    """Create a GitSyncService instance for testing."""
    return GitSyncService(
        git_processor=mock_git_processor,
        sync_interval=1,  # Short interval for testing
        max_retries=2,
        retry_delay=0.1
    )

@pytest.mark.asyncio
async def test_start_service(git_sync_service):
    """Test starting the sync service."""
    await git_sync_service.start()
    assert git_sync_service._running is True
    assert git_sync_service._task is not None
    await git_sync_service.stop()

@pytest.mark.asyncio
async def test_stop_service(git_sync_service):
    """Test stopping the sync service."""
    await git_sync_service.start()
    await git_sync_service.stop()
    assert git_sync_service._running is False
    assert git_sync_service._task is None or git_sync_service._task.done()

@pytest.mark.asyncio
async def test_sync_success(git_sync_service, mock_git_processor):
    """Test successful sync operation."""
    await git_sync_service.start()
    await asyncio.sleep(1.5)  # Wait for sync to occur
    
    mock_git_processor.push_changes.assert_called()
    await git_sync_service.stop()

@pytest.mark.asyncio
async def test_sync_retry_on_failure(git_sync_service, mock_git_processor):
    """Test retry behavior on sync failure."""
    # Make first attempt fail, second succeed
    mock_git_processor.push_changes.side_effect = [
        GitProcessingError("Network error"),
        None
    ]
    
    await git_sync_service.start()
    await asyncio.sleep(1.5)  # Wait for retry
    
    assert mock_git_processor.push_changes.call_count >= 2
    await git_sync_service.stop()

@pytest.mark.asyncio
async def test_sync_max_retries_exceeded(git_sync_service, mock_git_processor):
    """Test behavior when max retries are exceeded."""
    # Make all attempts fail
    mock_git_processor.push_changes.side_effect = GitProcessingError("Network error")
    
    await git_sync_service.start()
    await asyncio.sleep(2)  # Wait for all retries
    
    assert mock_git_processor.push_changes.call_count >= git_sync_service.max_retries
    await git_sync_service.stop()

@pytest.mark.asyncio
async def test_multiple_start_calls(git_sync_service):
    """Test handling of multiple start calls."""
    await git_sync_service.start()
    await git_sync_service.start()  # Should log warning
    assert git_sync_service._running is True
    await git_sync_service.stop()

@pytest.mark.asyncio
async def test_multiple_stop_calls(git_sync_service):
    """Test handling of multiple stop calls."""
    await git_sync_service.start()
    await git_sync_service.stop()
    await git_sync_service.stop()  # Should log warning
    assert git_sync_service._running is False

@pytest.mark.asyncio
async def test_commit_immediately_single_message(git_sync_service, mock_git_processor):
    """Test immediate commit of a single message file."""
    message_path = Path("/tmp/test-storage/messages/2024-01-11/message_123.json")
    
    await git_sync_service.commit_immediately(message_path)
    
    mock_git_processor.commit_message.assert_called_once_with(message_path)

@pytest.mark.asyncio
async def test_commit_immediately_multiple_media(git_sync_service, mock_git_processor):
    """Test immediate commit of multiple media files."""
    media_paths = [
        Path("/tmp/test-storage/media/2024-01-11/photo_123.jpg"),
        Path("/tmp/test-storage/media/2024-01-11/document_456.pdf")
    ]
    
    await git_sync_service.commit_immediately(media_paths, is_media=True)
    
    mock_git_processor.commit_media.assert_called_once_with(media_paths)

@pytest.mark.asyncio
async def test_commit_immediately_failure(git_sync_service, mock_git_processor):
    """Test handling of immediate commit failure."""
    message_path = Path("/tmp/test-storage/messages/2024-01-11/message_123.json")
    mock_git_processor.commit_message.side_effect = GitProcessingError("Git error")
    
    with pytest.raises(GitProcessingError):
        await git_sync_service.commit_immediately(message_path) 