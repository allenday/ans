"""Tests for git storage adapter."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from pathlib import Path
import yaml
import json
from datetime import datetime

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
def repo_mock():
    """Create a mock git repository."""
    mock = MagicMock(spec=Repo)
    mock.index = MagicMock()
    mock.index.add = MagicMock()
    mock.index.commit = MagicMock()
    mock.remotes = MagicMock()
    mock.remotes.origin = None
    return mock

@pytest.fixture
def git_adapter(base_path, repo_mock):
    """Create a git storage adapter with a mock repository."""
    with patch('chronicler.storage.git.Repo', autospec=True) as repo_cls_mock:
        repo_cls_mock.init = MagicMock(return_value=repo_mock)
        adapter = GitStorageAdapter(base_path)
        return adapter

@pytest.mark.asyncio
async def test_initialization(git_adapter, base_path, user, repo_mock):
    """Test initializing the git storage adapter."""
    # Execute
    result = await git_adapter.init_storage(user)
    
    # Verify repository structure was created
    repo_path = base_path / f"{user.id}_journal"
    assert repo_path.exists()
    assert (repo_path / "topics").exists()
    assert (repo_path / "metadata.yaml").exists()
    
    # Verify metadata file was created correctly
    with open(repo_path / "metadata.yaml") as f:
        metadata = yaml.safe_load(f)
        assert metadata['user_id'] == user.id
        assert metadata['topics'] == {}
    
    # Verify git repository was initialized
    repo_mock.index.add.assert_called_once_with(['topics', 'metadata.yaml'])
    repo_mock.index.commit.assert_called_once_with("Initial repository structure")
    
    # Verify adapter state
    assert git_adapter.is_initialized()
    assert result == git_adapter

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
            'topics': {'existing': {'name': 'Existing Topic'}}
        }, f)
    
    # Execute
    with patch('chronicler.storage.git.Repo', autospec=True) as repo_cls_mock:
        repo_cls_mock.return_value = repo_mock
        result = await git_adapter.init_storage(user)
    
    # Verify repository was not reinitialized
    repo_mock.index.add.assert_not_called()
    repo_mock.index.commit.assert_not_called()
    
    # Verify adapter state
    assert git_adapter.is_initialized()
    assert result == git_adapter

@pytest.mark.asyncio
async def test_create_topic(git_adapter, base_path, user, repo_mock):
    """Test creating a new topic."""
    # Initialize storage
    await git_adapter.init_storage(user)
    
    # Create test topic
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"source": "test"}
    )
    
    # Execute
    await git_adapter.create_topic(topic)
    
    # Verify topic directory was created
    repo_path = base_path / f"{user.id}_journal"
    topic_path = repo_path / "topics" / topic.id
    assert topic_path.exists()
    assert (topic_path / "messages.jsonl").exists()
    
    # Verify metadata was updated
    with open(repo_path / "metadata.yaml") as f:
        metadata = yaml.safe_load(f)
        assert topic.id in metadata['topics']
        assert metadata['topics'][topic.id]['name'] == topic.name
        assert metadata['topics'][topic.id]['source'] == "test"
    
    # Verify changes were committed
    repo_mock.index.add.assert_called_with([
        'topics/test_topic/messages.jsonl',
        'metadata.yaml'
    ])
    repo_mock.index.commit.assert_called_with(f"Created topic {topic.name}")

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
async def test_create_topic_missing_source(git_adapter, user):
    """Test creating a topic with chat_id but no source."""
    # Initialize storage
    await git_adapter.init_storage(user)
    
    # Create test topic with invalid metadata
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={"chat_id": "123"}
    )
    
    # Verify error is raised
    with pytest.raises(ValueError, match="Source must be specified when chat_id is present"):
        await git_adapter.create_topic(topic)

@pytest.mark.asyncio
async def test_save_message(git_adapter, base_path, user, repo_mock):
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
    
    # Verify message was saved
    messages_file = base_path / f"{user.id}_journal/topics/{topic.id}/messages.jsonl"
    with open(messages_file) as f:
        saved_message = json.loads(f.readline())
        assert saved_message['content'] == message.content
        assert saved_message['source'] == message.source
        assert saved_message['metadata'] == message.metadata
        assert saved_message['id'] == message.id
    
    # Verify changes were committed
    repo_mock.index.add.assert_called_with([f'topics/{topic.id}/messages.jsonl'])
    repo_mock.index.commit.assert_called_with(f"Added message to {topic.id}")

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
    
    # Verify message was saved with attachment reference
    messages_file = base_path / f"{user.id}_journal/topics/{topic.id}/messages.jsonl"
    with open(messages_file) as f:
        saved_message = json.loads(f.readline())
        assert saved_message['content'] == message.content
        assert saved_message['source'] == message.source
        assert saved_message['metadata'] == message.metadata
        assert saved_message['id'] == message.id
        assert len(saved_message['attachments']) == 1
        assert saved_message['attachments'][0]['id'] == attachment.id
        assert saved_message['attachments'][0]['type'] == attachment.type
        assert saved_message['attachments'][0]['filename'] == attachment.filename
    
    # Verify changes were committed
    repo_mock.index.add.assert_called_with([f'topics/{topic.id}/messages.jsonl'])
    repo_mock.index.commit.assert_called_with(f"Added message to {topic.id}")

@pytest.mark.asyncio
async def test_sync(git_adapter, user, repo_mock):
    """Test syncing with remote repository."""
    # Initialize storage
    await git_adapter.init_storage(user)
    
    # Set up mock remote
    remote_mock = MagicMock()
    repo_mock.remotes.origin = remote_mock
    
    # Execute
    await git_adapter.sync()
    
    # Verify remote was pulled and pushed
    remote_mock.pull.assert_called_once_with(rebase=True)
    remote_mock.push.assert_called_once_with()

@pytest.mark.asyncio
async def test_sync_no_remote(git_adapter, user):
    """Test syncing without a remote repository."""
    # Initialize storage
    await git_adapter.init_storage(user)
    
    # Verify error is raised
    with pytest.raises(RuntimeError, match="No remote repository configured"):
        await git_adapter.sync()

@pytest.mark.asyncio
async def test_set_github_config(git_adapter, user, repo_mock):
    """Test setting GitHub configuration."""
    # Initialize storage
    await git_adapter.init_storage(user)
    
    # Execute
    await git_adapter.set_github_config("test_token", "test/repo")
    
    # Verify remote was added
    repo_mock.create_remote.assert_called_once_with(
        "origin",
        "https://x-access-token:test_token@github.com/test/repo.git"
    ) 