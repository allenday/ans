"""Tests for storage coordinator."""
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from chronicler.storage.coordinator import StorageCoordinator
from chronicler.storage.interface import Topic, Message, Attachment, User

@pytest.fixture
def storage_path():
    """Create a test storage path."""
    return Path("/test/storage/path")

@pytest.fixture
def git_storage_mock():
    """Create a mock git storage adapter."""
    mock = AsyncMock()
    mock.init_storage = AsyncMock()
    mock.create_topic = AsyncMock()
    mock.save_message = AsyncMock()
    mock.sync = AsyncMock()
    mock.set_github_config = AsyncMock()
    return mock

@pytest.fixture
def file_storage_mock():
    """Create a mock file storage adapter."""
    mock = AsyncMock()
    mock.init_storage = AsyncMock()
    mock.create_topic = AsyncMock()
    mock.save_attachment = AsyncMock()
    return mock

@pytest.fixture
def attachment_handler_mock():
    """Create a mock attachment handler."""
    mock = AsyncMock()
    mock.process = AsyncMock(side_effect=lambda x: x)  # Return attachment unchanged
    return mock

@pytest.fixture
def coordinator(storage_path, git_storage_mock, file_storage_mock, attachment_handler_mock):
    """Create a storage coordinator with mocked dependencies."""
    with patch('chronicler.storage.coordinator.GitStorageAdapter') as git_mock, \
         patch('chronicler.storage.coordinator.FileSystemStorage') as file_mock, \
         patch('chronicler.storage.coordinator.TelegramAttachmentHandler') as handler_mock:
        
        git_mock.return_value = git_storage_mock
        file_mock.return_value = file_storage_mock
        handler_mock.return_value = attachment_handler_mock
        
        coordinator = StorageCoordinator(storage_path)
        return coordinator

@pytest.mark.asyncio
async def test_initialization(storage_path, git_storage_mock, file_storage_mock):
    """Test storage coordinator initialization."""
    with patch('chronicler.storage.coordinator.GitStorageAdapter') as git_mock, \
         patch('chronicler.storage.coordinator.FileSystemStorage') as file_mock:
        
        git_mock.return_value = git_storage_mock
        file_mock.return_value = file_storage_mock
        
        coordinator = StorageCoordinator(storage_path)
        
        # Verify storage adapters were initialized with correct path
        git_mock.assert_called_once_with(storage_path)
        file_mock.assert_called_once_with(storage_path)
        
        # Verify attributes were set
        assert coordinator.storage_path == storage_path
        assert coordinator.git_storage == git_storage_mock
        assert coordinator.file_storage == file_storage_mock
        assert not coordinator.is_initialized()

@pytest.mark.asyncio
async def test_init_storage(coordinator, git_storage_mock, file_storage_mock):
    """Test initializing storage."""
    user = User(id="test_user", name="Test User")
    
    # Execute
    result = await coordinator.init_storage(user)
    
    # Verify storage was initialized
    git_storage_mock.init_storage.assert_called_once_with(user)
    file_storage_mock.init_storage.assert_called_once_with(user)
    
    # Verify coordinator is initialized
    assert coordinator.is_initialized()
    assert result == coordinator

@pytest.mark.asyncio
async def test_init_storage_error(coordinator, git_storage_mock):
    """Test error handling when initializing storage."""
    git_storage_mock.init_storage.side_effect = RuntimeError("Test error")
    
    user = User(id="test_user", name="Test User")
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        await coordinator.init_storage(user)
    
    # Verify coordinator is not initialized
    assert not coordinator.is_initialized()

@pytest.mark.asyncio
async def test_create_topic(coordinator, git_storage_mock, file_storage_mock):
    """Test creating a topic."""
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"key": "value"}
    )
    
    # Execute
    topic_id = await coordinator.create_topic(topic)
    
    # Verify topic was created in both storages
    git_storage_mock.create_topic.assert_called_once_with(topic, False)
    file_storage_mock.create_topic.assert_called_once_with(topic, False)
    
    # Verify returned topic ID
    assert topic_id == topic.id

@pytest.mark.asyncio
async def test_create_topic_error(coordinator, git_storage_mock):
    """Test error handling when creating a topic."""
    git_storage_mock.create_topic.side_effect = RuntimeError("Test error")
    
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"key": "value"}
    )
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        await coordinator.create_topic(topic)

@pytest.mark.asyncio
async def test_create_topic_file_error(coordinator, git_storage_mock, file_storage_mock):
    """Test error handling when file storage fails to create topic."""
    file_storage_mock.create_topic.side_effect = RuntimeError("File storage error")
    
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"key": "value"}
    )
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="File storage error"):
        await coordinator.create_topic(topic)
    
    # Verify git storage was called
    git_storage_mock.create_topic.assert_called_once_with(topic, False)

@pytest.mark.asyncio
async def test_save_message_without_attachments(coordinator, git_storage_mock, file_storage_mock):
    """Test saving a message without attachments."""
    message = Message(
        content="Test message",
        source="test",
        metadata={"key": "value"}
    )
    
    # Execute
    await coordinator.save_message("test_topic", message)
    
    # Verify message was saved to git storage
    git_storage_mock.save_message.assert_called_once_with("test_topic", message)
    
    # Verify no attachments were saved
    file_storage_mock.save_attachment.assert_not_called()

@pytest.mark.asyncio
async def test_save_message_with_attachments(coordinator, git_storage_mock, file_storage_mock, attachment_handler_mock):
    """Test saving a message with attachments."""
    attachment = Attachment(
        id="test_attachment",
        type="text/plain",
        filename="test.txt",
        data=b"test data"
    )
    
    message = Message(
        content="Test message",
        source="test",
        metadata={"key": "value"},
        attachments=[attachment]
    )
    
    # Execute
    await coordinator.save_message("test_topic", message)
    
    # Verify attachment was processed
    attachment_handler_mock.process.assert_called_once_with(attachment)
    
    # Verify message was saved to git storage
    git_storage_mock.save_message.assert_called_once_with("test_topic", message)
    
    # Verify attachment was saved to file storage
    file_storage_mock.save_attachment.assert_called_once_with("test_topic", message.id, attachment)

@pytest.mark.asyncio
async def test_save_message_error(coordinator, git_storage_mock):
    """Test error handling when saving a message."""
    git_storage_mock.save_message.side_effect = RuntimeError("Test error")
    
    message = Message(
        content="Test message",
        source="test",
        metadata={"key": "value"}
    )
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        await coordinator.save_message("test_topic", message)

@pytest.mark.asyncio
async def test_save_message_attachment_error(coordinator, git_storage_mock, file_storage_mock):
    """Test error handling when saving message attachments."""
    file_storage_mock.save_attachment.side_effect = RuntimeError("File storage error")
    
    attachment = Attachment(
        id="test_attachment",
        type="text/plain",
        filename="test.txt",
        data=b"test data"
    )
    
    message = Message(
        content="Test message",
        source="test",
        metadata={"key": "value"},
        attachments=[attachment]
    )
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="File storage error"):
        await coordinator.save_message("test_topic", message)
    
    # Verify message was not saved to git storage
    git_storage_mock.save_message.assert_not_called()

@pytest.mark.asyncio
async def test_save_attachment(coordinator, file_storage_mock, attachment_handler_mock):
    """Test saving an attachment."""
    attachment = Attachment(
        id="test_attachment",
        type="text/plain",
        filename="test.txt",
        data=b"test data"
    )
    
    # Execute
    await coordinator.save_attachment("test_topic", "test_message", attachment)
    
    # Verify attachment was processed
    attachment_handler_mock.process.assert_called_once_with(attachment)
    
    # Verify attachment was saved
    file_storage_mock.save_attachment.assert_called_once_with("test_topic", "test_message", attachment)

@pytest.mark.asyncio
async def test_save_attachment_error(coordinator, file_storage_mock):
    """Test error handling when saving an attachment."""
    file_storage_mock.save_attachment.side_effect = RuntimeError("Test error")
    
    attachment = Attachment(
        id="test_attachment",
        type="text/plain",
        filename="test.txt",
        data=b"test data"
    )
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Test error"):
        await coordinator.save_attachment("test_topic", "test_message", attachment)

@pytest.mark.asyncio
async def test_sync(coordinator, git_storage_mock):
    """Test syncing with remote storage."""
    # Execute
    await coordinator.sync()
    
    # Verify sync was called
    git_storage_mock.sync.assert_called_once()

@pytest.mark.asyncio
async def test_sync_error(coordinator, git_storage_mock):
    """Test error handling when syncing with remote storage."""
    git_storage_mock.sync.side_effect = RuntimeError("Sync error")
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Sync error"):
        await coordinator.sync()

@pytest.mark.asyncio
async def test_set_github_config(coordinator, git_storage_mock):
    """Test setting GitHub configuration."""
    # Execute
    await coordinator.set_github_config("test_token", "test_repo")
    
    # Verify config was set
    git_storage_mock.set_github_config.assert_called_once_with("test_token", "test_repo")

@pytest.mark.asyncio
async def test_set_github_config_error(coordinator, git_storage_mock):
    """Test error handling when setting GitHub configuration."""
    git_storage_mock.set_github_config.side_effect = RuntimeError("Config error")
    
    # Verify error is propagated
    with pytest.raises(RuntimeError, match="Config error"):
        await coordinator.set_github_config("test_token", "test_repo") 