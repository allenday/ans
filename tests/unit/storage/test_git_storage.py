import pytest
import pytest_asyncio
import os
import shutil
from pathlib import Path
from datetime import datetime
from chronicler.storage.interface import User, Topic, Message, Attachment
from chronicler.storage.git import GitStorageAdapter
import yaml
import json
from unittest.mock import Mock, patch

@pytest.fixture
def test_repo_path(tmp_path):
    """Create a temporary repository path"""
    return tmp_path

@pytest_asyncio.fixture
async def storage(tmp_path):
    # Clean up any existing test data
    test_path = tmp_path / "test_user_journal"
    if test_path.exists():
        shutil.rmtree(test_path)
    
    # Create fresh storage adapter
    storage = GitStorageAdapter(tmp_path)
    user = User(id="test_user", name="Test User")
    await storage.init_storage(user)
    return storage

@pytest_asyncio.fixture
async def git_adapter_mock(test_repo_path):
    """Create a git storage adapter with mocked git operations"""
    # Clean up any existing test data
    test_path = test_repo_path / "test_user_journal"
    if test_path.exists():
        shutil.rmtree(test_path)
    
    # Create mock repo with properly configured index
    mock_repo = Mock()
    mock_repo.working_dir = str(test_path)  # Point to test_user_journal
    mock_repo.is_dirty = Mock(return_value=False)
    
    # Create mock index with proper method signatures
    mock_index = Mock()
    mock_index.add = Mock(return_value=None)
    mock_index.commit = Mock(return_value=None)
    mock_repo.index = mock_index
    
    # Start the patches
    repo_patcher = patch('chronicler.storage.git.Repo', autospec=True)
    mock_repo_class = repo_patcher.start()
    mock_repo_class.return_value = mock_repo
    mock_repo_class.init.return_value = mock_repo
    
    # Create adapter and initialize storage
    adapter = GitStorageAdapter(test_repo_path)  # Pass parent dir
    await adapter.init_storage(User(id="test_user", name="Test User"))
    
    # Reset mock call counts after initialization
    mock_index.add.reset_mock()
    mock_index.commit.reset_mock()
    
    yield adapter, mock_repo
    
    # Stop the patcher
    repo_patcher.stop()

@pytest.mark.asyncio
async def test_create_topic_with_name(storage):
    """Test that topics are created with correct name-based structure"""
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    await storage.create_topic(topic)
    
    # Verify directory structure
    topic_dir = storage.repo_path / "telegram" / "987654321" / "123456789"
    assert topic_dir.exists()
    assert (topic_dir / "messages.jsonl").exists()
    
    # Verify attachments directory exists
    attachments_dir = topic_dir / "attachments"
    assert attachments_dir.exists()
    
    # Verify metadata structure
    metadata_path = storage.repo_path / "metadata.yaml"
    with open(metadata_path) as f:
        metadata = yaml.safe_load(f)
    
    assert "sources" in metadata
    assert "telegram" in metadata["sources"]
    assert "groups" in metadata["sources"]["telegram"]
    assert "987654321" in metadata["sources"]["telegram"]["groups"]
    assert metadata["sources"]["telegram"]["groups"]["987654321"]["name"] == "Test Group"
    assert "123456789" in metadata["sources"]["telegram"]["groups"]["987654321"]["topics"]
    assert metadata["sources"]["telegram"]["groups"]["987654321"]["topics"]["123456789"]["name"] == "Test Topic"

@pytest.mark.asyncio
async def test_save_message_with_attachment(storage):
    """Test that messages with attachments are stored correctly"""
    # Create topic
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    await storage.create_topic(topic)
    
    # Create test attachment
    test_data = b"test image data"
    attachment = Attachment(
        id="AgACAgEAAx0CR2WwagADHGR_Y_h8zG4HMc5SdngsvciqrEgHowACGq0xG_2PiEdml3NAynBCrgEAAwIAA20AAzYE",
        type="image/jpeg",
        filename="test.jpg",
        data=test_data
    )
    
    # Create message with attachment
    message = Message(
        content="Test message with photo",
        source="test_user",
        timestamp=datetime.utcnow(),
        attachments=[attachment],
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    # Save message
    await storage.save_message("123456789", message)
    
    # Verify file structure
    topic_dir = storage.repo_path / "telegram" / "987654321" / "123456789"
    attachments_dir = topic_dir / "attachments" / "jpg"
    assert attachments_dir.exists()
    
    # Verify attachment file exists with file_id as name
    attachment_path = attachments_dir / f"{attachment.id}.jpg"
    assert attachment_path.exists()
    assert attachment_path.read_bytes() == test_data
    
    # Verify message in messages.jsonl
    messages_file = topic_dir / "messages.jsonl"
    assert messages_file.exists()
    with open(messages_file) as f:
        message_data = json.loads(f.read().strip())
        assert message_data["attachments"][0]["id"] == attachment.id
        assert message_data["attachments"][0]["original_name"] == "test.jpg"

@pytest.mark.asyncio
async def test_save_message_with_multiple_attachments(storage):
    """Test saving a message with multiple attachment types"""
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    await storage.create_topic(topic)
    
    # Create test attachments
    attachments = [
        Attachment(
            id="photo_AgACAgEAAx0CR2",
            type="image/jpeg",
            filename="test.jpg",
            data=b"test image"
        ),
        Attachment(
            id="doc_BQACAgEAAx0CR2",
            type="text/plain",
            filename="test.txt",
            data=b"test document"
        ),
        Attachment(
            id="sticker_CAACAgEAAx0",
            type="image/webp",
            filename="test.webp",
            data=b"test sticker"
        )
    ]
    
    message = Message(
        content="Test message with multiple attachments",
        source="test_user",
        timestamp=datetime.utcnow(),
        attachments=attachments,
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    await storage.save_message("123456789", message)
    
    # Verify all files exist in correct directories
    topic_dir = storage.repo_path / "telegram" / "987654321" / "123456789"
    assert (topic_dir / "attachments" / "jpg" / f"{attachments[0].id}.jpg").exists()
    assert (topic_dir / "attachments" / "txt" / f"{attachments[1].id}.txt").exists()
    assert (topic_dir / "attachments" / "webp" / f"{attachments[2].id}.webp").exists()
    
    # Verify message was saved with correct metadata
    messages_file = topic_dir / "messages.jsonl"
    assert messages_file.exists()
    with open(messages_file) as f:
        message_data = json.loads(f.read().strip())
        assert len(message_data["attachments"]) == 3
        for i, att in enumerate(message_data["attachments"]):
            assert att["id"] == attachments[i].id
            assert att["original_name"] == attachments[i].filename

@pytest.mark.asyncio
async def test_invalid_topic_name(storage):
    """Test that invalid topic names are rejected"""
    topic = Topic(
        id="123456789",
        name="invalid/topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    with pytest.raises(ValueError, match="Topic name cannot contain '/'"):
        await storage.create_topic(topic)

@pytest.mark.asyncio
async def test_duplicate_topic_name(storage):
    """Test that duplicate topic IDs are rejected"""
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    await storage.create_topic(topic)
    
    # Try to create another topic with same ID
    topic2 = Topic(
        id="123456789",
        name="Different Name",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    with pytest.raises(ValueError, match="Topic 123456789 already exists"):
        await storage.create_topic(topic2)

@pytest.mark.asyncio
async def test_save_message_nonexistent_topic(storage):
    """Test that saving to nonexistent topic fails"""
    message = Message(
        content="Test message",
        source="test_user",
        timestamp=datetime.utcnow(),
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    with pytest.raises(ValueError, match="Topic nonexistent does not exist"):
        await storage.save_message("nonexistent", message)

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_create_topic_with_git(git_adapter_mock):
    """Test creating a topic with git operations"""
    adapter, mock_repo = git_adapter_mock
    
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group",
            "description": "Test topic",
            "created": "2024-01-01"
        }
    )
    
    await adapter.create_topic(topic)
    
    # Verify directory was created
    topic_dir = adapter.repo_path / "telegram" / "987654321" / "123456789"
    assert topic_dir.exists()
    assert (topic_dir / "messages.jsonl").exists()
    assert (topic_dir / "attachments").exists()
    
    # Verify git operations - using relative paths as Git does
    mock_repo.index.add.assert_any_call(['telegram'])
    mock_repo.index.add.assert_any_call(['telegram/987654321'])
    mock_repo.index.add.assert_any_call(['telegram/987654321/123456789'])
    mock_repo.index.add.assert_any_call(['metadata.yaml'])
    mock_repo.index.commit.assert_called_once_with("Created topic: Test Topic")

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_message_with_git(git_adapter_mock):
    """Test saving a message with git operations"""
    adapter, mock_repo = git_adapter_mock
    
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group",
            "description": "Test topic"
        }
    )
    await adapter.create_topic(topic)
    
    message = Message(
        content="Test message",
        source="test",
        timestamp=datetime.utcnow(),
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    # Reset mock call counts after topic creation
    mock_repo.index.add.reset_mock()
    mock_repo.index.commit.reset_mock()
    
    await adapter.save_message(topic.id, message)
    
    # Verify message file exists
    topic_dir = adapter.repo_path / "telegram" / "987654321" / "123456789"
    messages_file = topic_dir / "messages.jsonl"
    assert messages_file.exists()
    
    # Verify git operations - using relative paths
    expected_paths = ["telegram/987654321/123456789/messages.jsonl"]
    mock_repo.index.add.assert_called_once_with(expected_paths)
    mock_repo.index.commit.assert_called_once_with("Added message to topic: Test Topic")

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_attachment_with_git(git_adapter_mock):
    """Test saving an attachment with git operations"""
    adapter, mock_repo = git_adapter_mock
    
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group",
            "description": "Test topic"
        }
    )
    await adapter.create_topic(topic)
    
    # Reset mock call counts after topic creation
    mock_repo.index.add.reset_mock()
    mock_repo.index.commit.reset_mock()
    
    attachment = Attachment(
        id="test_attachment",
        type="image/jpeg",
        filename="test.jpg",
        data=b"test content"
    )
    
    await adapter.save_attachment(topic.id, "msg_1", attachment)
    
    # Verify attachment file exists
    topic_dir = adapter.repo_path / "telegram" / "987654321" / "123456789"
    attachment_file = topic_dir / "attachments" / "jpg" / f"{attachment.id}.jpg"
    assert attachment_file.exists()
    
    # Verify git operations - using relative paths
    expected_path = f"telegram/987654321/123456789/attachments/jpg/{attachment.id}.jpg"
    mock_repo.index.add.assert_called_once_with([expected_path])
    mock_repo.index.commit.assert_called_once_with("Added attachment to topic: Test Topic")

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_message_with_attachment_with_git(git_adapter_mock):
    """Test saving a message with attachment with git operations"""
    adapter, mock_repo = git_adapter_mock
    
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group",
            "description": "Test topic"
        }
    )
    await adapter.create_topic(topic)
    
    # Reset mock call counts after topic creation
    mock_repo.index.add.reset_mock()
    mock_repo.index.commit.reset_mock()
    
    attachment = Attachment(
        id="test_attachment",
        type="image/jpeg",
        filename="test.jpg",
        data=b"test content"
    )
    
    message = Message(
        content="Test message with attachment",
        source="test",
        timestamp=datetime.utcnow(),
        attachments=[attachment],
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    await adapter.save_message(topic.id, message)
    
    # Verify files exist
    topic_dir = adapter.repo_path / "telegram" / "987654321" / "123456789"
    messages_file = topic_dir / "messages.jsonl"
    attachment_file = topic_dir / "attachments" / "jpg" / f"{attachment.id}.jpg"
    assert messages_file.exists()
    assert attachment_file.exists()
    
    # Verify git operations - using relative paths
    # Note: save_message may call add() multiple times, so we verify the final state
    mock_repo.index.add.assert_any_call([f"telegram/987654321/123456789/messages.jsonl"])
    mock_repo.index.add.assert_any_call([f"telegram/987654321/123456789/attachments/jpg/{attachment.id}.jpg"])
    mock_repo.index.commit.assert_called_once_with("Added message to topic: Test Topic") 