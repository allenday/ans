import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import yaml
import json
from datetime import datetime, timezone

from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.interface import User, Topic, Message, Attachment

@pytest.fixture
def storage_path(tmp_path):
    return tmp_path / "test_storage"

@pytest.fixture
def test_user():
    return User(id="test_user", name="Test User")

@pytest.fixture
def repo_mock():
    mock = AsyncMock()
    mock.git = AsyncMock()
    mock.remotes = {}
    mock.index = AsyncMock()
    mock.delete_remote = AsyncMock()
    mock.create_remote = AsyncMock()
    return mock

@pytest.fixture
def git_storage(storage_path, repo_mock):
    with patch('chronicler.storage.git.Repo') as repo_class_mock:
        repo_class_mock.init = MagicMock(return_value=repo_mock)
        repo_class_mock.return_value = repo_mock
        adapter = GitStorageAdapter(storage_path)
        yield adapter

@pytest.mark.asyncio
async def test_initialization(git_storage, test_user, repo_mock):
    """Test storage initialization"""
    await git_storage.init_storage(test_user)
    
    # Verify directories created
    assert (git_storage.repo_path / "topics").exists()
    assert (git_storage.repo_path / "metadata.yaml").exists()
    
    # Verify metadata file created with correct content
    with open(git_storage.repo_path / "metadata.yaml") as f:
        metadata = yaml.safe_load(f)
        assert metadata['user_id'] == test_user.id
        assert metadata['topics'] == {}
    
    # Verify git operations
    repo_mock.index.add.assert_called_with(['topics', 'metadata.yaml'])
    repo_mock.index.commit.assert_called_with("Initial repository structure")

@pytest.mark.asyncio
async def test_create_topic(git_storage, test_user):
    """Test topic creation"""
    await git_storage.init_storage(test_user)
    
    topic = Topic(id="test_topic", name="Test Topic")
    await git_storage.create_topic(topic)
    
    # Verify topic directory structure
    topic_path = git_storage.repo_path / "topics" / str(topic.id)
    assert topic_path.exists()
    assert (topic_path / "messages.jsonl").exists()
    assert (topic_path / "attachments").exists()
    
    # Verify metadata updated
    with open(git_storage.repo_path / "metadata.yaml") as f:
        metadata = yaml.safe_load(f)
        assert str(topic.id) in metadata['topics']
        assert metadata['topics'][str(topic.id)]['name'] == topic.name

@pytest.mark.asyncio
async def test_create_topic_with_source(git_storage, test_user):
    """Test topic creation with source and chat_id"""
    await git_storage.init_storage(test_user)
    
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={
            'source': 'telegram',
            'chat_id': '123456',
            'chat_title': 'Test Chat'
        }
    )
    await git_storage.create_topic(topic)
    
    # Verify topic directory structure
    topic_path = git_storage.repo_path / "telegram" / "123456" / str(topic.id)
    assert topic_path.exists()
    assert (topic_path / "messages.jsonl").exists()
    assert (topic_path / "attachments").exists()
    
    # Verify metadata updated
    with open(git_storage.repo_path / "metadata.yaml") as f:
        metadata = yaml.safe_load(f)
        assert 'telegram' in metadata['sources']
        assert '123456' in metadata['sources']['telegram']['groups']
        assert str(topic.id) in metadata['sources']['telegram']['groups']['123456']['topics']

@pytest.mark.asyncio
async def test_save_message(git_storage, test_user):
    """Test saving a message to a topic"""
    await git_storage.init_storage(test_user)
    
    # Create topic first
    topic = Topic(id="test_topic", name="Test Topic")
    await git_storage.create_topic(topic)
    
    # Create and save message
    message = Message(
        content="Test message",
        source="test",
        timestamp=datetime.now(timezone.utc)
    )
    await git_storage.save_message(str(topic.id), message)
    
    # Verify message saved
    messages_file = git_storage.repo_path / "topics" / str(topic.id) / "messages.jsonl"
    with open(messages_file) as f:
        saved_message = json.loads(f.readline())
        assert saved_message['content'] == message.content
        assert saved_message['source'] == message.source

@pytest.mark.asyncio
async def test_save_message_with_attachments(git_storage, test_user):
    """Test saving a message with attachments"""
    await git_storage.init_storage(test_user)
    
    # Create topic first
    topic = Topic(id="test_topic", name="Test Topic")
    await git_storage.create_topic(topic)
    
    # Create message with attachment
    attachment = Attachment(
        id="test_attachment",
        type="image/jpeg",
        filename="test.jpg",
        data=b"test data"
    )
    message = Message(
        content="Test message with attachment",
        source="test",
        timestamp=datetime.now(timezone.utc),
        attachments=[attachment]
    )
    
    await git_storage.save_message(str(topic.id), message)
    
    # Verify attachment saved
    attachment_path = git_storage.repo_path / "topics" / str(topic.id) / "media" / "jpg" / "test_attachment.jpg"
    assert attachment_path.exists()
    with open(attachment_path, 'rb') as f:
        assert f.read() == b"test data"
    
    # Verify message saved with attachment reference
    messages_file = git_storage.repo_path / "topics" / str(topic.id) / "messages.jsonl"
    with open(messages_file) as f:
        saved_message = json.loads(f.readline())
        assert saved_message['content'] == message.content
        assert len(saved_message['attachments']) == 1
        assert saved_message['attachments'][0]['id'] == attachment.id

@pytest.mark.asyncio
async def test_sync_no_remote(git_storage, test_user):
    """Test sync with no remote configured"""
    await git_storage.init_storage(test_user)
    await git_storage.sync()  # Should not raise an error

@pytest.mark.asyncio
async def test_sync_with_remote(git_storage, repo_mock):
    """Test syncing with remote repository"""
    # Set up remote
    repo_mock.remotes = {'origin': AsyncMock()}
    
    # Call sync
    await git_storage.sync()
    
    # Verify push was called
    repo_mock.git.push.assert_called_once_with('-f', 'origin', 'main')

@pytest.mark.asyncio
async def test_set_github_config(git_storage, repo_mock, storage_path):
    """Test setting GitHub configuration"""
    # Set up initialized state
    git_storage._initialized = True
    git_storage._repo = repo_mock
    git_storage.repo_path = storage_path
    
    # Create metadata file
    metadata_path = storage_path / "metadata.yaml"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(yaml.dump({}))
    
    # Call set_github_config
    await git_storage.set_github_config("test_token", "test/repo")
    
    # Verify remote was created with correct URL
    repo_mock.create_remote.assert_called_once_with(
        'origin', 
        'https://test_token@github.com/test/repo.git'
    )

@pytest.mark.asyncio
async def test_create_topic_invalid_name(git_storage, test_user):
    """Test topic creation with invalid name"""
    await git_storage.init_storage(test_user)
    
    topic = Topic(id="test_topic", name="Invalid/Name")
    with pytest.raises(ValueError, match="Topic name cannot contain '/'"):
        await git_storage.create_topic(topic)

@pytest.mark.asyncio
async def test_create_topic_already_exists(git_storage, test_user):
    """Test topic creation when topic already exists"""
    await git_storage.init_storage(test_user)
    
    topic = Topic(id="test_topic", name="Test Topic")
    await git_storage.create_topic(topic)
    
    with pytest.raises(ValueError, match="Topic test_topic already exists"):
        await git_storage.create_topic(topic)

@pytest.mark.asyncio
async def test_create_topic_invalid_metadata(git_storage, test_user):
    """Test topic creation with invalid metadata"""
    await git_storage.init_storage(test_user)
    
    topic = Topic(
        id="test_topic",
        name="Test Topic",
        metadata={'chat_id': '123456'}  # Missing source
    )
    with pytest.raises(ValueError, match="Source must be specified when chat_id is present"):
        await git_storage.create_topic(topic)

@pytest.mark.asyncio
async def test_save_message_nonexistent_topic(git_storage, test_user):
    """Test saving message to nonexistent topic"""
    await git_storage.init_storage(test_user)
    
    message = Message(
        content="Test message",
        source="test",
        timestamp=datetime.now(timezone.utc)
    )
    with pytest.raises(ValueError, match="Topic nonexistent does not exist"):
        await git_storage.save_message("nonexistent", message)

@pytest.mark.asyncio
async def test_save_message_invalid_metadata(git_storage, test_user):
    """Test saving message with invalid metadata"""
    await git_storage.init_storage(test_user)
    
    topic = Topic(id="test_topic", name="Test Topic")
    await git_storage.create_topic(topic)
    
    message = Message(
        content="Test message",
        source="test",
        timestamp=datetime.now(timezone.utc),
        metadata={'chat_id': '123456'}  # Missing source
    )
    with pytest.raises(ValueError, match="Source must be specified when chat_id is present"):
        await git_storage.save_message(str(topic.id), message)

@pytest.mark.asyncio
async def test_save_attachment_nonexistent_topic(git_storage, test_user):
    """Test saving attachment to nonexistent topic"""
    await git_storage.init_storage(test_user)
    
    attachment = Attachment(
        id="test_attachment",
        type="image/jpeg",
        filename="test.jpg",
        data=b"test data"
    )
    with pytest.raises(ValueError, match="Topic nonexistent does not exist"):
        await git_storage.save_attachment("nonexistent", "message_id", attachment)

@pytest.mark.asyncio
async def test_sync_error(git_storage, repo_mock):
    """Test error handling during sync"""
    # Set up remote and make push fail
    repo_mock.remotes = {'origin': AsyncMock()}
    repo_mock.git.push.side_effect = Exception("Push failed")
    git_storage._repo = repo_mock
    
    # Verify error is propagated
    with pytest.raises(Exception, match="Push failed"):
        await git_storage.sync()

@pytest.mark.asyncio
async def test_set_github_config_not_initialized(git_storage):
    """Test setting GitHub config before initialization"""
    with pytest.raises(RuntimeError, match="Must initialize repository first"):
        await git_storage.set_github_config("test_token", "test/repo")

@pytest.mark.asyncio
async def test_save_message_with_binary_attachment(git_storage, test_user):
    """Test saving message with binary attachment"""
    await git_storage.init_storage(test_user)
    
    topic = Topic(id="test_topic", name="Test Topic")
    await git_storage.create_topic(topic)
    
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
    
    await git_storage.save_message(str(topic.id), message)
    
    # Verify attachment saved with correct extension
    attachment_path = git_storage.repo_path / "topics" / str(topic.id) / "media" / "bin" / "test_attachment.bin"
    assert attachment_path.exists()
    with open(attachment_path, 'rb') as f:
        assert f.read() == b"binary data" 