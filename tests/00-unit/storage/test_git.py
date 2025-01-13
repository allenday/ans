"""Tests for git storage adapter."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from pathlib import Path
import yaml
import json
from datetime import datetime, timezone

from git import Repo
from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.interface import User, Topic, Message, Attachment

@pytest.fixture
def base_path(tmp_path):
    """Create a temporary base path for testing."""
    return tmp_path

@pytest.fixture
def user():
    """Create a test user."""
    return User(
        id="test_user",
        name="Test User",
        metadata={"key": "value"}
    )

@pytest.fixture
def repo_mock(monkeypatch):
    """Create a mock git repo."""
    mock = MagicMock(spec=Repo)
    mock.working_dir = None  # Will be set by the adapter
    mock.index = MagicMock()
    mock.index.add = MagicMock()
    mock.index.commit = MagicMock()
    mock.remotes = {}
    
    def mock_init(*args, **kwargs):
        return mock
        
    monkeypatch.setattr(Repo, 'init', mock_init)
    return mock

@pytest.fixture
def git_adapter(base_path, repo_mock):
    """Create a git storage adapter with a mock repository."""
    with patch('chronicler.storage.git.Repo', autospec=True) as repo_cls_mock:
        repo_cls_mock.init = MagicMock(return_value=repo_mock)
        adapter = GitStorageAdapter(base_path)
        adapter.repo_path = base_path / "test_user_journal"
        return adapter

@pytest.mark.asyncio
async def test_initialization(git_adapter, user, repo_mock):
    """Test initializing storage."""
    # Execute
    await git_adapter.init_storage(user)

    # Verify
    repo_mock.index.add.assert_called_with(['.'])
    repo_mock.index.commit.assert_called_with("Initialize repository")

@pytest.mark.asyncio
async def test_initialization_existing_repo(git_adapter, base_path, user, repo_mock):
    """Test initializing with an existing repository."""
    # Create existing repository structure
    repo_path = base_path / f"{user.id}_journal"
    repo_path.mkdir(parents=True)
    (repo_path / ".git").mkdir()
    (repo_path / "topics").mkdir()
    
    with open(repo_path / "metadata.yaml", 'w') as f:
        yaml.dump({
            'user_id': user.id,
            'topics': {'existing': {'name': 'Existing Topic'}},
            'sources': {}
        }, f)
    
    # Execute
    with patch('chronicler.storage.git.Repo', autospec=True) as repo_cls_mock:
        repo_cls_mock.return_value = repo_mock
        await git_adapter.init_storage(user)
    
    # Verify repository was not reinitialized
    repo_mock.index.add.assert_not_called()
    repo_mock.index.commit.assert_not_called()
    
    # Verify adapter state
    assert git_adapter.is_initialized()

@pytest.mark.asyncio
async def test_create_topic(git_adapter, user, repo_mock):
    """Test creating a topic with source."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"source": "test"}
    )
    await git_adapter.create_topic(topic)

    # Verify topic was created correctly
    repo_mock.index.add.assert_called_with(['.'])
    repo_mock.index.commit.assert_called_with("Created topic Test Topic")

@pytest.mark.asyncio
async def test_create_topic_no_source(git_adapter, user, repo_mock):
    """Test creating a topic without a source."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic"
    )
    await git_adapter.create_topic(topic)

    # Verify
    repo_mock.index.add.assert_called_with(['.'])
    repo_mock.index.commit.assert_called_with("Created topic Test Topic")

@pytest.mark.asyncio
async def test_create_topic_invalid_name(git_adapter, user):
    """Test creating a topic with an invalid name."""
    # Initialize storage
    await git_adapter.init_storage(user)
    
    # Create test topic with invalid name
    topic = Topic(
        id="test_topic",
        name="Invalid/Name",
        metadata={"source": "test"}
    )
    
    # Verify error is raised
    with pytest.raises(ValueError, match="Topic name cannot contain '/'"):
        await git_adapter.create_topic(topic)

@pytest.mark.asyncio
async def test_create_topic_missing_source(git_adapter, user, repo_mock):
    """Test creating a topic with chat_id but no source."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"chat_id": "123"}
    )

    # Verify error is raised
    with pytest.raises(ValueError, match="Source must be specified when chat_id is present"):
        await git_adapter.create_topic(topic)

@pytest.mark.asyncio
async def test_create_topic_already_exists(git_adapter, user, repo_mock):
    """Test creating a topic that already exists."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic"
    )

    # Create metadata file with existing topic
    metadata_path = git_adapter.repo_path / "metadata.json"
    metadata = {
        'user_id': user.id,
        'topics': {
            'test_topic': {
                'name': 'Test Topic',
                'created_at': datetime.now().isoformat(),
                'path': str(topic.id)
            }
        }
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)

    # Verify error is raised
    with pytest.raises(ValueError, match="Topic test_topic already exists"):
        await git_adapter.create_topic(topic)

@pytest.mark.asyncio
async def test_save_message(git_adapter, user, repo_mock):
    """Test saving a message to a topic."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"source": "test"}
    )
    await git_adapter.create_topic(topic)

    # Create test message
    message = Message(
        content="Test message",
        source="test",
        metadata={"key": "value"}
    )

    # Execute
    await git_adapter.save_message(topic.id, message)

    # Verify
    repo_mock.index.add.assert_called_with(['.'])
    repo_mock.index.commit.assert_called_with(f"Added message {message.id} to topic {topic.id}")

@pytest.mark.asyncio
async def test_save_message_with_attachments(git_adapter, base_path, user, repo_mock):
    """Test saving a message with attachments."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"source": "test"}
    )
    await git_adapter.create_topic(topic)

    # Create test message with attachment
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
    await git_adapter.save_message(topic.id, message)

    # Verify
    repo_mock.index.add.assert_called_with(['.'])
    repo_mock.index.commit.assert_called_with(f"Added message {message.id} to topic {topic.id}")

@pytest.mark.asyncio
async def test_save_message_with_binary_attachment(git_adapter, user, repo_mock):
    """Test saving message with binary attachment."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic"
    )
    await git_adapter.create_topic(topic)

    # Create message with attachment
    attachment = Attachment(
        id="test_attachment",
        type="application/octet-stream",
        filename="test.bin",
        data=b"binary data"
    )
    message = Message(
        content="Test message with binary attachment",
        source="test",
        timestamp=datetime.now(timezone.utc),
        attachments=[attachment]
    )

    # Execute
    await git_adapter.save_message(str(topic.id), message)

    # Verify
    attachment_path = git_adapter.repo_path / topic.id / "media" / "application" / f"test_attachment.bin"
    assert attachment_path.parent.exists()
    assert attachment_path.exists()
    assert attachment_path.read_bytes() == b"binary data"

@pytest.mark.asyncio
async def test_save_message_invalid_metadata(git_adapter, user, repo_mock):
    """Test saving message with invalid metadata."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic"
    )
    await git_adapter.create_topic(topic)

    # Create message with invalid metadata
    message = Message(
        content="Test message",
        source="test",
        timestamp=datetime.now(timezone.utc),
        metadata={'chat_id': '123456'}  # Missing source
    )

    # Verify error is raised
    with pytest.raises(ValueError, match="Source must be specified when chat_id is present"):
        await git_adapter.save_message(str(topic.id), message)

@pytest.mark.asyncio
async def test_sync_no_remote(git_adapter, user):
    """Test sync with no remote configured."""
    # Initialize storage
    await git_adapter.init_storage(user)

    # Verify error is raised
    with pytest.raises(RuntimeError, match="No remote repository configured"):
        await git_adapter.sync()

@pytest.mark.asyncio
async def test_sync_with_remote(git_adapter, repo_mock):
    """Test syncing with remote repository."""
    # Set up remote
    remote_mock = MagicMock()
    remote_mock.push = MagicMock()
    repo_mock.remotes = {'origin': remote_mock}
    git_adapter._repo = repo_mock
    git_adapter._initialized = True

    # Execute
    await git_adapter.sync()

    # Verify
    remote_mock.push.assert_called_once()

@pytest.mark.asyncio
async def test_sync_error(git_adapter, repo_mock):
    """Test error handling during sync."""
    # Set up remote and make push fail
    remote_mock = MagicMock()
    remote_mock.push.side_effect = Exception("Push failed")
    repo_mock.remotes = {'origin': remote_mock}
    git_adapter._repo = repo_mock
    git_adapter._initialized = True

    # Verify error is propagated
    with pytest.raises(Exception, match="Push failed"):
        await git_adapter.sync()

@pytest.mark.asyncio
async def test_set_github_config(git_adapter, repo_mock):
    """Test setting GitHub configuration."""
    # Set up initialized state
    git_adapter._initialized = True
    git_adapter._repo = repo_mock

    # Execute
    await git_adapter.set_github_config("test_token", "test/repo")

    # Verify remote was created with correct URL
    repo_mock.create_remote.assert_called_once_with(
        'origin',
        'https://x-access-token:test_token@github.com/test/repo.git'
    )

@pytest.mark.asyncio
async def test_set_github_config_not_initialized(git_adapter):
    """Test setting GitHub config before initialization."""
    with pytest.raises(RuntimeError, match="Must initialize repository first"):
        await git_adapter.set_github_config("test_token", "test/repo")

@pytest.mark.asyncio
async def test_await_uninitialized(git_adapter):
    """Test awaiting uninitialized adapter."""
    with pytest.raises(RuntimeError, match="Must call init_storage()"):
        await git_adapter

@pytest.mark.asyncio
async def test_await_initialized(git_adapter, user):
    """Test awaiting initialized adapter."""
    await git_adapter.init_storage(user)
    adapter = await git_adapter
    assert adapter == git_adapter

@pytest.mark.asyncio
async def test_save_message_topic_not_exists(git_adapter, user):
    """Test saving message to non-existent topic."""
    await git_adapter.init_storage(user)
    
    message = Message(
        content="Test message",
        source="test",
        metadata={"key": "value"}
    )
    
    with pytest.raises(ValueError, match="Topic test_topic does not exist"):
        await git_adapter.save_message("test_topic", message)

@pytest.mark.asyncio
async def test_save_message_missing_topic_dir(git_adapter, user, repo_mock):
    """Test saving message when topic directory is missing."""
    await git_adapter.init_storage(user)
    
    # Create topic in metadata but not on disk
    metadata = {
        'user_id': user.id,
        'topics': {
            'test_topic': {
                'name': 'Test Topic',
                'created_at': datetime.now().isoformat(),
                'path': 'test_topic'
            }
        }
    }
    metadata_path = git_adapter.repo_path / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    
    message = Message(
        content="Test message",
        source="test",
        metadata={"key": "value"}
    )
    
    with pytest.raises(RuntimeError, match="Topic directory .* does not exist"):
        await git_adapter.save_message("test_topic", message)

@pytest.mark.asyncio
async def test_save_attachment_topic_not_exists(git_adapter, user):
    """Test saving attachment to non-existent topic."""
    await git_adapter.init_storage(user)
    
    attachment = Attachment(
        id="test_attachment",
        type="text/plain",
        filename="test.txt",
        data=b"test data"
    )
    
    with pytest.raises(ValueError, match="Topic test_topic does not exist"):
        await git_adapter.save_attachment("test_topic", "test_message", attachment)

@pytest.mark.asyncio
async def test_save_attachment_missing_topic_dir(git_adapter, user, repo_mock):
    """Test saving attachment when topic directory is missing."""
    await git_adapter.init_storage(user)
    
    # Create topic in metadata but not on disk
    metadata = {
        'user_id': user.id,
        'topics': {
            'test_topic': {
                'name': 'Test Topic',
                'created_at': datetime.now().isoformat(),
                'path': 'test_topic'
            }
        }
    }
    metadata_path = git_adapter.repo_path / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    
    attachment = Attachment(
        id="test_attachment",
        type="text/plain",
        filename="test.txt",
        data=b"test data"
    )
    
    with pytest.raises(RuntimeError, match="Topic directory .* does not exist"):
        await git_adapter.save_attachment("test_topic", "test_message", attachment)

@pytest.mark.asyncio
async def test_read_metadata_missing_file(git_adapter, user):
    """Test reading metadata when file is missing."""
    await git_adapter.init_storage(user)
    
    # Remove metadata file
    metadata_path = git_adapter.repo_path / "metadata.json"
    metadata_path.unlink()
    
    # Read metadata should return empty dict
    metadata = await git_adapter._read_metadata()
    assert metadata == {'user_id': None, 'topics': {}}