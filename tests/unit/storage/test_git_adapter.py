import pytest
import pytest_asyncio
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.interface import Message, Attachment, User, Topic

@pytest.fixture
def test_repo_path(tmp_path):
    """Create a temporary repository path"""
    return tmp_path / "test_repo"

@pytest.fixture
def test_user():
    """Create a test user"""
    return User(id="test_user", name="Test User")

@pytest_asyncio.fixture
async def git_adapter(test_repo_path, test_user):
    """Create a git storage adapter"""
    adapter = GitStorageAdapter(test_repo_path)
    await adapter.init_storage(test_user)
    return adapter

@pytest_asyncio.fixture
async def git_adapter_sync(test_repo_path, test_user):
    """Create a git storage adapter synchronously"""
    adapter = GitStorageAdapter(test_repo_path)
    await adapter.init_storage(test_user)
    return adapter

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_create_topic(git_adapter_sync, test_user):
    """Test creating a topic"""
    adapter = git_adapter_sync
    
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
    
    topic_dir = adapter.repo_path / "telegram" / "987654321" / "123456789"
    assert topic_dir.exists()
    assert topic_dir.is_dir()
    assert (topic_dir / "messages.jsonl").exists()
    assert (topic_dir / "attachments").exists()

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_message(git_adapter_sync, test_user):
    """Test saving a message"""
    adapter = git_adapter_sync
    
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
    
    await adapter.save_message(topic.id, message)
    
    topic_dir = adapter.repo_path / "telegram" / "987654321" / "123456789"
    assert (topic_dir / "messages.jsonl").exists()

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_attachment(git_adapter):
    """Test saving an attachment"""
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
    await git_adapter.create_topic(topic)
    
    attachment = Attachment(
        id="test_attachment",
        type="image/jpeg",
        filename="test.jpg",
        data=b"test content"
    )
    
    await git_adapter.save_attachment(topic.id, "msg_1", attachment)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    attachments_dir = topic_dir / "attachments" / "jpg"
    assert attachments_dir.exists()
    assert (attachments_dir / "test_attachment.jpg").exists()

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_message_with_attachment(git_adapter):
    """Test saving a message with attachment"""
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
    await git_adapter.create_topic(topic)
    
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
    
    await git_adapter.save_message(topic.id, message)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    assert (topic_dir / "messages.jsonl").exists()
    attachments_dir = topic_dir / "attachments" / "jpg"
    assert attachments_dir.exists()
    assert (attachments_dir / "test_attachment.jpg").exists()

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_multiple_messages(git_adapter):
    """Test saving multiple messages"""
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
    await git_adapter.create_topic(topic)
    
    messages = [
        Message(
            content=f"Message {i}",
            source="test",
            timestamp=datetime.utcnow(),
            metadata={
                "source": "telegram",
                "chat_id": "987654321",
                "chat_title": "Test Group"
            }
        )
        for i in range(3)
    ]
    
    for message in messages:
        await git_adapter.save_message(topic.id, message)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    messages_file = topic_dir / "messages.jsonl"
    assert messages_file.exists()
    with open(messages_file) as f:
        lines = f.readlines()
        assert len(lines) == 3

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_message_with_multiple_attachments(git_adapter):
    """Test saving a message with multiple attachments"""
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
    await git_adapter.create_topic(topic)
    
    attachments = [
        Attachment(id=f"att{i}", type="image/jpeg", filename=f"test{i}.jpg", data=b"test")
        for i in range(3)
    ]
    
    message = Message(
        content="Test message with attachments",
        source="test",
        timestamp=datetime.utcnow(),
        attachments=attachments,
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    await git_adapter.save_message(topic.id, message)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    attachments_dir = topic_dir / "attachments" / "jpg"
    assert len(list(attachments_dir.glob("*.jpg"))) == 3

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_large_message(git_adapter):
    """Test saving a large message"""
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
    await git_adapter.create_topic(topic)
    
    large_content = "x" * 1024 * 1024  # 1MB of content
    message = Message(
        content=large_content,
        source="test",
        timestamp=datetime.utcnow(),
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    await git_adapter.save_message(topic.id, message)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    messages_file = topic_dir / "messages.jsonl"
    assert messages_file.exists()

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_save_binary_attachment(git_adapter):
    """Test saving a binary attachment"""
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
    await git_adapter.create_topic(topic)
    
    binary_content = bytes([i % 256 for i in range(1024)])
    attachment = Attachment(
        id="binary_test",
        type="application/octet-stream",
        filename="test.bin",
        data=binary_content
    )
    
    await git_adapter.save_attachment(topic.id, "msg_1", attachment)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    attachments_dir = topic_dir / "attachments" / "bin"
    assert (attachments_dir / "binary_test.bin").exists()

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_topic_directory_permissions(git_adapter):
    """Test topic directory permissions"""
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
    await git_adapter.create_topic(topic)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    assert topic_dir.exists()
    assert topic_dir.is_dir()
    # Check that directory is readable and writable
    assert os.access(str(topic_dir), os.R_OK | os.W_OK)

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_empty_message_content(git_adapter):
    """Test saving a message with empty content"""
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
    await git_adapter.create_topic(topic)
    
    message = Message(
        content="",
        source="test",
        timestamp=datetime.utcnow(),
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    await git_adapter.save_message(topic.id, message)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    messages_file = topic_dir / "messages.jsonl"
    assert messages_file.exists()

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_unicode_content(git_adapter):
    """Test saving a message with unicode content"""
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
    await git_adapter.create_topic(topic)
    
    message = Message(
        content="Hello 👋 World 🌍",
        source="test",
        timestamp=datetime.utcnow(),
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    
    await git_adapter.save_message(topic.id, message)
    
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    messages_file = topic_dir / "messages.jsonl"
    assert messages_file.exists()

@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.asyncio
async def test_create_topic_ignore_exists(git_adapter):
    """Test creating a topic that already exists"""
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group",
            "description": "Test topic",
            "created": "2024-01-01",
            "updated": "2024-01-01"
        }
    )
    
    # Create topic twice
    await git_adapter.create_topic(topic)
    await git_adapter.create_topic(topic, ignore_exists=True)
    
    # Should not raise an error
    topic_dir = git_adapter.repo_path / "telegram" / "987654321" / "123456789"
    assert topic_dir.exists() 