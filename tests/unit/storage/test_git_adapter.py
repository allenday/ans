import pytest
import pytest_asyncio
from pathlib import Path
import yaml
from datetime import datetime
import json

from chronicler.storage.interface import User, Topic, Message, Attachment
from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.messages import MessageStore

# Define test categories
pytestmark = pytest.mark.unit  # All tests in this file are unit tests by default

@pytest_asyncio.fixture
async def storage(tmp_path):
    """Provides a GitStorageAdapter instance"""
    adapter = GitStorageAdapter(base_path=tmp_path)
    user = User(id="test_user", name="Test User")
    await adapter.init_storage(user)
    return adapter  # Return the adapter directly, not a coroutine

@pytest.mark.asyncio
async def test_init_storage(tmp_path):
    """Test storage initialization"""
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
async def test_create_topic(storage):
    """Test topic creation"""
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
async def test_save_message(storage):
    """Test saving a message to a topic"""
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
async def test_save_attachment(storage):
    """Test attachment saving"""
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
async def test_save_message_with_attachment(storage):
    """Test saving message with attachment reference"""
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
async def test_init_storage_twice(tmp_path):
    """Test initializing storage multiple times"""
    adapter = GitStorageAdapter(base_path=tmp_path)
    user = User(id="test_user", name="Test User")
    
    # First initialization
    await adapter.init_storage(user)
    first_commit_hash = adapter._repo.head.commit.hexsha
    
    # Second initialization shouldn't create new commit
    await adapter.init_storage(user)
    second_commit_hash = adapter._repo.head.commit.hexsha
    
    assert first_commit_hash == second_commit_hash

@pytest.mark.asyncio
async def test_create_topic_with_metadata(storage):
    """Test creating topic with additional metadata"""
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
async def test_save_message_to_nonexistent_topic(storage):
    """Test saving message to non-existent topic raises error"""
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
async def test_save_attachment_without_data(storage):
    """Test saving attachment without binary data"""
    adapter = await storage  # Get the actual adapter from the fixture
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
async def test_save_multiple_messages(storage):
    """Test saving multiple messages to the same topic"""
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
async def test_save_message_with_multiple_attachments(storage):
    """Test saving message with multiple attachments"""
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
async def test_create_topic_with_invalid_id(storage):
    """Test creating topic with invalid characters in ID"""
    adapter = await storage
    topic = Topic(id="invalid/id", name="Test Topic")
    with pytest.raises(ValueError):
        await adapter.create_topic(topic)

@pytest.mark.unit
@pytest.mark.slow  # For large file tests
@pytest.mark.asyncio
async def test_save_large_message(storage):
    """Test saving a large message"""
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
async def test_save_binary_attachment(storage):
    """Test saving binary attachment with various content types"""
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
async def test_topic_directory_permissions(storage):
    """Test that created directories have correct permissions"""
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    topic_path = adapter.repo_path / "topics" / topic.id
    media_path = topic_path / "media"
    
    # Check directory permissions (should be readable/writable by user)
    assert topic_path.stat().st_mode & 0o777 == 0o755
    assert media_path.stat().st_mode & 0o777 == 0o755 

@pytest.mark.asyncio
async def test_create_duplicate_topic(storage):
    """Test creating a topic that already exists"""
    adapter = await storage
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    # Try to create same topic again
    with pytest.raises(ValueError):
        await adapter.create_topic(topic)

@pytest.mark.asyncio
async def test_save_attachment_invalid_topic(storage):
    """Test saving attachment to non-existent topic"""
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
async def test_invalid_base_path(tmp_path):
    """Test initializing storage with invalid base path"""
    nonexistent_path = tmp_path / "nonexistent"
    adapter = GitStorageAdapter(base_path=nonexistent_path)
    user = User(id="test_user", name="Test User")
    
    # Should create the base path
    await adapter.init_storage(user)
    assert nonexistent_path.exists()

@pytest.mark.asyncio
async def test_empty_message_content(storage):
    """Test saving message with empty content"""
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
async def test_unicode_content(storage):
    """Test handling of unicode content in messages"""
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
async def test_create_topic_ignore_exists(storage):
    """Test creating a topic that already exists with ignore_exists=True"""
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