"""Tests for storage processor."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, ANY
from chronicler.pipeline import TextFrame, ImageFrame
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.processors.git_processor import GitProcessor

@pytest.fixture
def storage_path(tmp_path):
    """Create a temporary storage path."""
    return tmp_path / "storage"

@pytest.fixture
def mock_storage():
    """Create a mock StorageCoordinator."""
    mock = Mock()
    mock.init_storage = Mock()
    mock.create_topic = Mock(return_value="test_topic")
    mock.save_message = Mock(return_value=Path("/tmp/storage/messages/test.json"))
    return mock

@pytest.fixture
def mock_git_processor():
    """Create a mock GitProcessor."""
    return Mock(spec=GitProcessor)

@pytest.fixture
def storage_processor(storage_path, mock_storage):
    """Create a StorageProcessor with mocked storage."""
    with patch('chronicler.processors.storage_processor.StorageCoordinator', return_value=mock_storage):
        return StorageProcessor(storage_path)

@pytest.fixture
def git_enabled_processor(storage_path, mock_storage, mock_git_processor):
    """Create a StorageProcessor with git enabled."""
    env_vars = {
        'GIT_REPO_URL': 'https://github.com/test/repo.git',
        'GIT_BRANCH': 'main',
        'GIT_USERNAME': 'testuser',
        'GIT_ACCESS_TOKEN': 'testtoken'
    }
    
    with patch.dict('os.environ', env_vars), \
         patch('chronicler.processors.storage_processor.StorageCoordinator', return_value=mock_storage), \
         patch('chronicler.processors.storage_processor.GitProcessor', return_value=mock_git_processor):
        return StorageProcessor(storage_path)

class TestStorageProcessor:
    """Test suite for StorageProcessor."""
    
    async def test_init_without_git(self, storage_processor):
        """Test initialization without git configuration."""
        assert storage_processor.git_processor is None
    
    async def test_init_with_git(self, git_enabled_processor, mock_git_processor):
        """Test initialization with git configuration."""
        assert git_enabled_processor.git_processor == mock_git_processor
    
    async def test_process_text_frame_without_git(self, storage_processor, mock_storage):
        """Test processing text frame without git."""
        frame = TextFrame("test message")
        frame.metadata = {'chat_id': 123, 'thread_id': 456, 'chat_title': 'Test Chat'}
        
        await storage_processor.process_frame(frame)
        
        mock_storage.save_message.assert_called_once()
    
    async def test_process_text_frame_with_git(self, git_enabled_processor, mock_storage, mock_git_processor):
        """Test processing text frame with git."""
        frame = TextFrame("test message")
        frame.metadata = {'chat_id': 123, 'thread_id': 456, 'chat_title': 'Test Chat'}
        message_path = Path("/tmp/storage/messages/test.json")
        mock_storage.save_message.return_value = message_path
        
        await git_enabled_processor.process_frame(frame)
        
        mock_storage.save_message.assert_called_once()
        mock_git_processor.commit_message.assert_called_once_with(message_path)
    
    async def test_process_image_frame_with_git(self, git_enabled_processor, mock_storage, mock_git_processor):
        """Test processing image frame with git."""
        frame = ImageFrame(b"test_image_data", "jpg")
        frame.metadata = {'chat_id': 123, 'thread_id': 456, 'chat_title': 'Test Chat'}
        message_path = Path("/tmp/storage/messages/test.json")
        media_paths = [Path("/tmp/storage/media/test.jpg")]
        mock_storage.save_message.return_value = (message_path, media_paths)
        
        await git_enabled_processor.process_frame(frame)
        
        mock_storage.save_message.assert_called_once()
        mock_git_processor.commit_message.assert_called_once_with(message_path)
        mock_git_processor.commit_media.assert_called_once_with(media_paths)
    
    async def test_git_commit_failure_doesnt_break_processing(self, git_enabled_processor, mock_storage, mock_git_processor):
        """Test that git commit failures don't break message processing."""
        frame = TextFrame("test message")
        frame.metadata = {'chat_id': 123, 'thread_id': 456, 'chat_title': 'Test Chat'}
        mock_git_processor.commit_message.side_effect = Exception("Git error")
        
        # Should not raise exception
        await git_enabled_processor.process_frame(frame)
        
        mock_storage.save_message.assert_called_once()
        mock_git_processor.commit_message.assert_called_once()
    
    async def test_git_processor_initialization_failure(self, storage_path, mock_storage):
        """Test handling of git processor initialization failure."""
        env_vars = {
            'GIT_REPO_URL': 'https://github.com/test/repo.git',
            'GIT_BRANCH': 'main',
            'GIT_USERNAME': 'testuser',
            'GIT_ACCESS_TOKEN': 'testtoken'
        }
        
        with patch.dict('os.environ', env_vars), \
             patch('chronicler.processors.storage_processor.StorageCoordinator', return_value=mock_storage), \
             patch('chronicler.processors.storage_processor.GitProcessor', side_effect=Exception("Git init error")):
            processor = StorageProcessor(storage_path)
            assert processor.git_processor is None 