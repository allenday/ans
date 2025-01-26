"""Tests for storage coordinator."""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime, timezone

from chronicler.storage.coordinator import StorageCoordinator
from chronicler.storage.git import GitStorageAdapter

@pytest.fixture
def base_path():
    """Create a test base path."""
    return Path("/test/storage/path")

@pytest.fixture
def git_storage_mock():
    """Create a mock git storage adapter."""
    mock = MagicMock()
    mock.init_storage = MagicMock()
    mock.create_topic = MagicMock()
    mock.save_message = MagicMock()
    mock.save_attachment = MagicMock()
    mock.sync = MagicMock()
    mock.set_github_config = MagicMock()
    mock.topic_exists = MagicMock(return_value=True)
    return mock

@pytest.fixture
def coordinator(base_path, git_storage_mock):
    """Create a storage coordinator with mocked dependencies."""
    with patch('chronicler.storage.coordinator.GitStorageAdapter') as git_mock:
        git_mock.return_value = git_storage_mock
        coordinator = StorageCoordinator(base_path)
        return coordinator

def test_initialization(base_path, git_storage_mock):
    """Test storage coordinator initialization."""
    with patch('chronicler.storage.coordinator.GitStorageAdapter') as git_mock:
        git_mock.return_value = git_storage_mock
        
        coordinator = StorageCoordinator(base_path)
        
        # Verify storage adapter was initialized with correct path
        git_mock.assert_called_once_with(base_path)
        
        # Verify attributes were set
        assert coordinator.base_path == base_path
        assert coordinator.git_storage == git_storage_mock

def test_init_storage(coordinator, git_storage_mock):
    """Test initializing storage."""
    user_id = 123
    
    # Execute
    coordinator.init_storage(user_id)
    
    # Verify storage was initialized
    git_storage_mock.init_storage.assert_called_once_with(user_id)

def test_init_storage_error(coordinator, git_storage_mock):
    """Test error handling when initializing storage."""
    git_storage_mock.init_storage.side_effect = RuntimeError("Test error")
    
    user_id = 123
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        coordinator.init_storage(user_id)

def test_create_topic(coordinator, git_storage_mock):
    """Test creating a topic."""
    user_id = 123
    topic_name = "test_topic"
    
    # Execute
    coordinator.create_topic(user_id, topic_name)
    
    # Verify topic was created
    git_storage_mock.create_topic.assert_called_once_with(user_id, topic_name)

def test_create_topic_error(coordinator, git_storage_mock):
    """Test error handling when creating a topic."""
    git_storage_mock.create_topic.side_effect = RuntimeError("Test error")
    
    user_id = 123
    topic_name = "test_topic"
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        coordinator.create_topic(user_id, topic_name)

def test_save_message(coordinator, git_storage_mock):
    """Test saving a message."""
    user_id = 123
    topic_name = "test_topic"
    message = {
        "content": "Test message",
        "source": "test",
        "metadata": {"key": "value"}
    }
    
    # Execute
    coordinator.save_message(user_id, topic_name, message)
    
    # Verify message was saved
    git_storage_mock.save_message.assert_called_once_with(user_id, topic_name, message)

def test_save_message_error(coordinator, git_storage_mock):
    """Test error handling when saving a message."""
    git_storage_mock.save_message.side_effect = RuntimeError("Test error")
    
    user_id = 123
    topic_name = "test_topic"
    message = {
        "content": "Test message",
        "source": "test",
        "metadata": {"key": "value"}
    }
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        coordinator.save_message(user_id, topic_name, message)

def test_save_attachment(coordinator, git_storage_mock):
    """Test saving an attachment."""
    user_id = 123
    topic_name = "test_topic"
    file_path = "/path/to/file.txt"
    attachment_name = "file.txt"
    
    # Execute
    coordinator.save_attachment(user_id, topic_name, file_path, attachment_name)
    
    # Verify attachment was saved
    git_storage_mock.save_attachment.assert_called_once_with(user_id, topic_name, file_path, attachment_name)

def test_save_attachment_error(coordinator, git_storage_mock):
    """Test error handling when saving an attachment."""
    git_storage_mock.save_attachment.side_effect = RuntimeError("Test error")
    
    user_id = 123
    topic_name = "test_topic"
    file_path = "/path/to/file.txt"
    attachment_name = "file.txt"
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        coordinator.save_attachment(user_id, topic_name, file_path, attachment_name)

def test_sync(coordinator, git_storage_mock):
    """Test syncing with remote storage."""
    user_id = 123
    
    # Execute
    coordinator.sync(user_id)
    
    # Verify sync was called
    git_storage_mock.sync.assert_called_once_with(user_id)

def test_sync_error(coordinator, git_storage_mock):
    """Test error handling when syncing with remote storage."""
    git_storage_mock.sync.side_effect = RuntimeError("Sync error")
    
    user_id = 123
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Sync error"):
        coordinator.sync(user_id)

def test_set_github_config(coordinator, git_storage_mock):
    """Test setting GitHub configuration."""
    # Execute
    coordinator.set_github_config("test_token", "test_repo")
    
    # Verify config was set
    git_storage_mock.set_github_config.assert_called_once_with("test_token", "test_repo")

def test_set_github_config_error(coordinator, git_storage_mock):
    """Test error handling when setting GitHub configuration."""
    git_storage_mock.set_github_config.side_effect = RuntimeError("Config error")
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Config error"):
        coordinator.set_github_config("test_token", "test_repo")

def test_topic_exists(coordinator, git_storage_mock):
    """Test checking if a topic exists."""
    user_id = 123
    topic_name = "test_topic"
    
    # Execute
    result = coordinator.topic_exists(user_id, topic_name)
    
    # Verify topic_exists was called
    git_storage_mock.topic_exists.assert_called_once_with(user_id, topic_name)
    assert result is True

def test_topic_exists_error(coordinator, git_storage_mock):
    """Test error handling when checking if a topic exists."""
    git_storage_mock.topic_exists.side_effect = RuntimeError("Test error")
    
    user_id = 123
    topic_name = "test_topic"
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        coordinator.topic_exists(user_id, topic_name) 