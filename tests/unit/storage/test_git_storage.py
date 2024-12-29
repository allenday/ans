import pytest
import pytest_asyncio
import os
from pathlib import Path
from datetime import datetime
from chronicler.storage.interface import User, Topic, Message, Attachment
from chronicler.storage.git import GitStorageAdapter

@pytest_asyncio.fixture
async def storage(tmp_path):
    storage = GitStorageAdapter(tmp_path)
    user = User(id="test_user", name="Test User")
    await storage.init_storage(user)
    return storage

@pytest.mark.asyncio
async def test_create_topic_with_name(storage):
    """Test that topics are created with correct name-based structure"""
    topic = Topic(id="test-topic", name="Test Topic")
    await storage.create_topic(topic)
    
    # Verify directory structure
    topic_dir = storage.repo_path / "topics" / "Test Topic"
    assert topic_dir.exists()
    assert (topic_dir / "messages.jsonl").exists()
    
    # Verify media directory exists
    media_dir = topic_dir / "media"
    assert media_dir.exists()

@pytest.mark.asyncio
async def test_save_message_with_attachment(storage):
    """Test that messages with attachments are stored correctly"""
    # Create topic
    topic = Topic(id="test-topic", name="Test Topic")
    await storage.create_topic(topic)
    
    # Create test attachment
    test_data = b"test image data"
    attachment = Attachment(
        id="photo_123",
        type="image/jpeg",
        filename="test.jpg",
        data=test_data
    )
    
    # Create message with attachment
    message = Message(
        content="Test message with photo",
        source="test_user",
        timestamp=datetime.utcnow(),
        attachments=[attachment]
    )
    
    # Save message
    await storage.save_message(topic.id, message)
    
    # Verify file structure
    topic_dir = storage.repo_path / "topics" / "Test Topic"
    media_dir = topic_dir / "media" / "jpg"
    assert media_dir.exists()
    assert (media_dir / "test.jpg").exists()
    assert (media_dir / "test.jpg").read_bytes() == test_data
    
    # Verify message in messages directory
    assert (topic_dir / "messages.jsonl").exists()

@pytest.mark.asyncio
async def test_save_message_with_multiple_attachments(storage):
    """Test saving a message with multiple attachment types"""
    topic = Topic(id="test-topic", name="Test Topic")
    await storage.create_topic(topic)
    
    # Create test attachments
    attachments = [
        Attachment(
            id="photo_123",
            type="image/jpeg",
            filename="test.jpg",
            data=b"test image"
        ),
        Attachment(
            id="doc_456",
            type="text/plain",
            filename="test.txt",
            data=b"test document"
        ),
        Attachment(
            id="sticker_789",
            type="image/webp",
            filename="test.webp",
            data=b"test sticker"
        )
    ]
    
    message = Message(
        content="Test message with multiple attachments",
        source="test_user",
        timestamp=datetime.utcnow(),
        attachments=attachments
    )
    
    await storage.save_message(topic.id, message)
    
    # Verify all files exist in correct directories
    topic_dir = storage.repo_path / "topics" / "Test Topic"
    assert (topic_dir / "media" / "jpg" / "test.jpg").exists()
    assert (topic_dir / "media" / "txt" / "test.txt").exists()
    assert (topic_dir / "media" / "webp" / "test.webp").exists()
    
    # Verify message was saved
    assert (topic_dir / "messages.jsonl").exists()

@pytest.mark.asyncio
async def test_invalid_topic_name(storage):
    """Test that invalid topic names are rejected"""
    topic = Topic(id="123", name="invalid/topic")
    with pytest.raises(ValueError, match="Topic name cannot contain '/'"):
        await storage.create_topic(topic)

@pytest.mark.asyncio
async def test_duplicate_topic_name(storage):
    """Test that duplicate topic names are rejected"""
    topic = Topic(id="123", name="test-topic")
    await storage.create_topic(topic)
    
    # Try to create another topic with same name but different ID
    topic2 = Topic(id="456", name="test-topic")
    with pytest.raises(ValueError, match="Topic test-topic already exists"):
        await storage.create_topic(topic2)

@pytest.mark.asyncio
async def test_save_message_nonexistent_topic(storage):
    """Test that saving to nonexistent topic fails"""
    message = Message(
        content="Test message",
        source="test_user",
        timestamp=datetime.utcnow()
    )
    
    with pytest.raises(ValueError, match="Topic nonexistent does not exist"):
        await storage.save_message("nonexistent", message) 