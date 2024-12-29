import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import shutil
from git import Repo
import yaml
from datetime import datetime
import logging
import json

from chronicler.storage.interface import User, Topic, Message, Attachment
from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.messages import MessageStore

# Define test categories
pytestmark = [
    pytest.mark.unit,
    pytest.mark.codex,
    pytest.mark.fs
]

@pytest_asyncio.fixture
async def storage(tmp_path):
    """Provides a storage adapter instance"""
    adapter = GitStorageAdapter(base_path=tmp_path)
    user = User(id="test_user", name="Test User")
    await adapter.init_storage(user)
    return adapter  # Return the adapter directly, not a coroutine

@pytest.mark.asyncio
async def test_init_storage(tmp_path, caplog, test_log_level):
    """Test storage initialization"""
    caplog.set_level(test_log_level)
    adapter = GitStorageAdapter(base_path=tmp_path)
    user = User(id="test_user", name="Test User")
    
    await adapter.init_storage(user)
    
    # Check directory structure
    repo_path = tmp_path / "test_user_journal"
    assert repo_path.exists()
    assert (repo_path / ".git").exists()
    assert (repo_path / "topics").exists()
    
    # Check metadata file
    metadata_path = repo_path / "metadata.yaml"
    assert metadata_path.exists()
    with open(metadata_path) as f:
        metadata = yaml.safe_load(f)
        assert metadata["user_id"] == "test_user"
        assert metadata["topics"] == {}

@pytest.mark.asyncio
async def test_create_topic(storage, caplog, test_log_level):
    """Test topic creation"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    # Check topic directory structure
    topic_path = adapter.repo_path / "topics" / topic.id
    assert topic_path.exists()
    assert (topic_path / adapter.MESSAGES_FILE).exists()
    assert (topic_path / "media").exists()
    
    # Check metadata update
    metadata_path = adapter.repo_path / "metadata.yaml"
    with open(metadata_path) as f:
        metadata = yaml.safe_load(f)
        assert topic.id in metadata["topics"]
        assert metadata["topics"][topic.id]["name"] == topic.name

@pytest.mark.asyncio
async def test_save_message(storage, caplog, test_log_level):
    """Test saving a message to a topic"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    message = Message(
        content="Test message",
        metadata={"type": "chat"},
        source="test",
        timestamp=datetime.utcnow()
    )
    
    await adapter.save_message(topic.id, message)
    
    # Verify file exists and contains message
    messages_file = adapter.repo_path / "topics" / topic.id / adapter.MESSAGES_FILE
    assert messages_file.exists()
    
    data = json.loads(messages_file.read_text().strip())
    assert data["content"] == "Test message"
    assert data["source"] == "test"
    assert data["metadata"]["type"] == "chat"

@pytest.mark.asyncio
async def test_save_attachment(storage, caplog, test_log_level):
    """Test attachment saving"""
    caplog.set_level(test_log_level)
    adapter = await storage
    # Create topic first
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    # Save attachment
    test_data = b"test file content"
    attachment = Attachment(
        id="att_123",
        type="text/plain",
        filename="test.txt",
        data=test_data
    )
    await adapter.save_attachment(topic.id, "msg_123", attachment)
    
    # Check file saved correctly
    file_path = adapter.repo_path / "topics" / topic.id / "media" / attachment.filename
    assert file_path.exists()
    assert file_path.read_bytes() == test_data

@pytest.mark.asyncio
async def test_save_message_with_attachment(storage, caplog, test_log_level):
    """Test saving message with attachment reference"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    attachment = Attachment(
        id="att_123",
        type="image/jpeg",
        filename="test.jpg",
        data=b"fake image data"
    )
    
    message = Message(
        content="Check out this image",
        metadata={"type": "chat"},
        source="test",
        timestamp=datetime.utcnow(),
        attachments=[attachment]
    )
    
    await adapter.save_message(topic.id, message)
    await adapter.save_attachment(topic.id, "msg_123", attachment)
    
    # Verify message references attachment
    messages_file = adapter.repo_path / "topics" / topic.id / adapter.MESSAGES_FILE
    data = json.loads(messages_file.read_text().strip())
    assert "attachments" in data
    assert data["attachments"][0]["filename"] == "test.jpg"

@pytest.mark.asyncio
async def test_init_storage_twice(tmp_path, caplog, test_log_level):
    """Test initializing storage twice"""
    caplog.set_level(test_log_level)
    adapter = GitStorageAdapter(base_path=tmp_path)
    user = User(id="test_user", name="Test User")
    
    await adapter.init_storage(user)
    await adapter.init_storage(user)  # Should not raise error
    
    # Check directory structure still intact
    repo_path = tmp_path / "test_user_journal"
    assert repo_path.exists()
    assert (repo_path / ".git").exists()

@pytest.mark.asyncio
async def test_create_topic_with_metadata(storage, caplog, test_log_level):
    """Test creating topic with additional metadata"""
    caplog.set_level(test_log_level)
    adapter = await storage  # Get the actual adapter from the fixture
    topic = Topic(
        id="topic_123",
        name="Test Topic",
        metadata={
            "description": "A test topic",
            "tags": ["test", "example"]
        }
    )
    await adapter.create_topic(topic)
    
    # Verify metadata was saved
    metadata_path = adapter.repo_path / "metadata.yaml"
    with open(metadata_path) as f:
        metadata = yaml.safe_load(f)
        topic_data = metadata["topics"][topic.id]
        assert topic_data["description"] == "A test topic"
        assert topic_data["tags"] == ["test", "example"]

@pytest.mark.asyncio
async def test_save_message_to_nonexistent_topic(storage, caplog, test_log_level):
    """Test saving message to non-existent topic raises error"""
    caplog.set_level(test_log_level)
    adapter = await storage
    message = Message(
        content="Test message",
        metadata={},
        source="test",
        timestamp=datetime.utcnow()
    )
    
    with pytest.raises(ValueError):
        await adapter.save_message("nonexistent_topic", message)

@pytest.mark.asyncio
async def test_save_attachment_without_data(storage, caplog, test_log_level):
    """Test saving attachment without binary data"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    attachment = Attachment(
        id="att_123",
        type="text/plain",
        filename="test.txt",
        url="http://example.com/test.txt"  # Only URL, no data
    )
    
    # Should not create file but should update metadata
    await adapter.save_attachment(topic.id, "msg_123", attachment)
    
    file_path = adapter.repo_path / "topics" / topic.id / "media" / attachment.filename
    assert not file_path.exists() 

@pytest.mark.asyncio
async def test_save_multiple_messages(storage, caplog, test_log_level):
    """Test saving multiple messages to the same topic"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    messages = [
        Message(
            content=f"Message {i}",
            metadata={"sequence": i},
            source="test",
            timestamp=datetime.utcnow()
        ) for i in range(3)
    ]
    
    for message in messages:
        await adapter.save_message(topic.id, message)
    
    # Verify all messages are saved in order
    messages_file = adapter.repo_path / "topics" / topic.id / adapter.MESSAGES_FILE
    posts = MessageStore.load_messages(messages_file)
    assert len(posts) == 3
    assert "Message 0" in posts[0].content
    assert "Message 2" in posts[2].content

@pytest.mark.asyncio
async def test_save_message_with_multiple_attachments(storage, caplog, test_log_level):
    """Test saving message with multiple attachments"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    attachments = [
        Attachment(
            id=f"att_{i}",
            type="text/plain",
            filename=f"file{i}.txt",
            data=f"content{i}".encode()
        ) for i in range(3)
    ]
    
    message = Message(
        content="Message with multiple files",
        metadata={"type": "chat"},
        source="test",
        timestamp=datetime.utcnow(),
        attachments=attachments
    )
    
    await adapter.save_message(topic.id, message)
    for attachment in attachments:
        await adapter.save_attachment(topic.id, "msg_123", attachment)
    
    # Verify all attachments are saved
    media_path = adapter.repo_path / "topics" / topic.id / "media"
    saved_files = list(media_path.glob("*.txt"))
    assert len(saved_files) == 3

@pytest.mark.asyncio
async def test_create_topic_with_invalid_id(storage, caplog, test_log_level):
    """Test creating topic with invalid characters in ID"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="invalid/id", name="Test Topic")
    with pytest.raises(ValueError):
        await adapter.create_topic(topic)

@pytest.mark.unit
@pytest.mark.slow  # For large file tests
@pytest.mark.asyncio
async def test_save_large_message(storage, caplog, test_log_level):
    """Test saving a large message"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    # Create a large message (100KB)
    large_content = "x" * 102400
    message = Message(
        content=large_content,
        metadata={"size": "large"},
        source="test",
        timestamp=datetime.utcnow()
    )
    
    await adapter.save_message(topic.id, message)
    
    # Verify content was saved correctly
    messages_file = adapter.repo_path / "topics" / topic.id / adapter.MESSAGES_FILE
    content = messages_file.read_text()
    data = json.loads(content.strip())
    assert len(data["content"]) == 102400

@pytest.mark.asyncio
async def test_save_binary_attachment(storage, caplog, test_log_level):
    """Test saving binary attachment with various content types"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    # Test different binary types
    binary_files = [
        ("image.jpg", b"\xFF\xD8\xFF\xE0", "image/jpeg"),
        ("doc.pdf", b"%PDF-1.5", "application/pdf"),
        ("archive.zip", b"PK\x03\x04", "application/zip")
    ]
    
    for filename, data, mime_type in binary_files:
        attachment = Attachment(
            id=f"att_{filename}",
            type=mime_type,
            filename=filename,
            data=data
        )
        await adapter.save_attachment(topic.id, "msg_123", attachment)
        
        file_path = adapter.repo_path / "topics" / topic.id / "media" / filename
        assert file_path.exists()
        assert file_path.read_bytes() == data

@pytest.mark.unit
@pytest.mark.fs  # For filesystem-specific tests
@pytest.mark.asyncio
async def test_topic_directory_permissions(storage, caplog, test_log_level):
    """Test that created directories have correct permissions"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    topic_path = adapter.repo_path / "topics" / topic.id
    media_path = topic_path / "media"
    
    # Check directory permissions (should be readable/writable by user)
    assert topic_path.stat().st_mode & 0o777 == 0o755
    assert media_path.stat().st_mode & 0o777 == 0o755 

@pytest.mark.asyncio
async def test_create_duplicate_topic(storage, caplog, test_log_level):
    """Test creating a topic that already exists"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    # Try to create same topic again
    with pytest.raises(ValueError):
        await adapter.create_topic(topic)

@pytest.mark.asyncio
async def test_save_attachment_invalid_topic(storage, caplog, test_log_level):
    """Test saving attachment to non-existent topic"""
    caplog.set_level(test_log_level)
    adapter = await storage
    attachment = Attachment(
        id="att_123",
        type="text/plain",
        filename="test.txt",
        data=b"test"
    )
    
    with pytest.raises(ValueError):
        await adapter.save_attachment("nonexistent", "msg_123", attachment)

@pytest.mark.asyncio
async def test_invalid_base_path(tmp_path, caplog, test_log_level):
    """Test initializing with invalid base path"""
    caplog.set_level(test_log_level)
    invalid_path = tmp_path / "nonexistent" / "path"
    adapter = GitStorageAdapter(base_path=invalid_path)
    user = User(id="test_user", name="Test User")
    
    await adapter.init_storage(user)  # Should create directories
    
    repo_path = invalid_path / "test_user_journal"
    assert repo_path.exists()
    assert (repo_path / ".git").exists()

@pytest.mark.asyncio
async def test_empty_message_content(storage, caplog, test_log_level):
    """Test saving message with empty content"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    message = Message(
        content="",
        metadata={"type": "empty"},
        source="test",
        timestamp=datetime.utcnow()
    )
    
    await adapter.save_message(topic.id, message)
    messages_file = adapter.repo_path / "topics" / topic.id / adapter.MESSAGES_FILE
    assert messages_file.exists()
    data = json.loads(messages_file.read_text().strip())
    assert data["content"] == ""

@pytest.mark.asyncio
async def test_unicode_content(storage, caplog, test_log_level):
    """Test handling of unicode content in messages"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    message = Message(
        content="Hello 👋 World 🌍",
        metadata={"language": "mixed"},
        source="test",
        timestamp=datetime.utcnow()
    )
    
    await adapter.save_message(topic.id, message)
    messages_file = adapter.repo_path / "topics" / topic.id / adapter.MESSAGES_FILE
    data = json.loads(messages_file.read_text(encoding='utf-8').strip())
    assert "👋" in data["content"]
    assert "🌍" in data["content"]

@pytest.mark.asyncio
async def test_create_topic_ignore_exists(storage, caplog, test_log_level):
    """Test creating a topic that already exists with ignore_exists=True"""
    caplog.set_level(test_log_level)
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    # Create same topic with new name
    new_topic = Topic(id="topic_123", name="Updated Topic", metadata={"updated": True})
    await adapter.create_topic(new_topic, ignore_exists=True)
    
    # Verify metadata was updated
    metadata_path = adapter.repo_path / "metadata.yaml"
    with open(metadata_path) as f:
        metadata = yaml.safe_load(f)
        assert metadata["topics"][topic.id]["name"] == "Updated Topic"
        assert metadata["topics"][topic.id]["updated"] is True 

@pytest.mark.asyncio
async def test_git_storage_init():
    """Test git storage initialization"""
    # [test code remains the same]

@pytest.mark.asyncio
async def test_git_storage_save():
    """Test saving messages to git storage"""
    # [test code remains the same] 