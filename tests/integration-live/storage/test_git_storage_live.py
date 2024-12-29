import pytest
import pytest_asyncio
import os
from pathlib import Path
from datetime import datetime
import yaml
from git import Repo
from chronicler.storage.interface import User, Topic, Message, Attachment
from chronicler.storage.git import GitStorageAdapter

def verify_metadata_yaml(repo_path: Path, topic_id: str = None, topic_name: str = None):
    """Helper to verify metadata.yaml contents"""
    metadata_path = repo_path / "metadata.yaml"
    assert metadata_path.exists(), "metadata.yaml should exist"
    
    with open(metadata_path) as f:
        metadata = yaml.safe_load(f)
    
    assert 'user_id' in metadata, "metadata should contain user_id"
    assert metadata['user_id'] == "test_user"
    assert 'topics' in metadata, "metadata should contain topics"
    
    if topic_id and topic_name:
        assert topic_id in metadata['topics'], f"metadata should contain topic {topic_id}"
        assert metadata['topics'][topic_id]['name'] == topic_name
        assert 'created_at' in metadata['topics'][topic_id]
        assert 'path' in metadata['topics'][topic_id]

@pytest_asyncio.fixture
async def storage(tmp_path):
    """Create a real GitStorageAdapter with a real git repo"""
    # Create storage adapter
    storage = GitStorageAdapter(tmp_path)
    user = User(id="test_user", name="Test User")
    await storage.init_storage(user)
    
    # Verify initial metadata
    repo_path = tmp_path / "test_user_journal"
    verify_metadata_yaml(repo_path)
    
    return storage, repo_path

@pytest.mark.asyncio
async def test_topic_creation_live(storage):
    """Test that topic creation works with real git repo"""
    storage_adapter, repo_path = storage
    topic = Topic(id="123", name="test-topic")
    await storage_adapter.create_topic(topic)
    
    # Verify directory structure
    topic_path = repo_path / "topics" / "test-topic"
    assert topic_path.exists(), "Topic directory should exist"
    assert (topic_path / "messages.jsonl").exists(), "Messages file should exist"
    assert (topic_path / "media").exists(), "Media directory should exist"
    
    # Verify git status
    repo = Repo(repo_path)
    assert not repo.is_dirty(), "Repository should be clean after commit"
    
    # Verify metadata
    verify_metadata_yaml(repo_path, "123", "test-topic")

@pytest.mark.asyncio
async def test_message_save_live(storage):
    """Test that message saving works with real git repo"""
    storage_adapter, repo_path = storage
    # Create topic
    topic = Topic(id="123", name="test-topic")
    await storage_adapter.create_topic(topic)
    
    # Create and save message
    message = Message(
        content="Test message",
        source="test_user",
        timestamp=datetime.utcnow()
    )
    await storage_adapter.save_message("123", message)
    
    # Verify message file
    messages_file = repo_path / "topics" / "test-topic" / "messages.jsonl"
    assert messages_file.exists(), "Messages file should exist"
    with open(messages_file) as f:
        content = f.read()
        assert "Test message" in content, "Message content should be in file"
    
    # Verify git status
    repo = Repo(repo_path)
    assert not repo.is_dirty(), "Repository should be clean after commit"
    
    # Verify metadata
    verify_metadata_yaml(repo_path, "123", "test-topic")

@pytest.mark.asyncio
async def test_attachment_save_live(storage):
    """Test that attachment saving works with real git repo"""
    storage_adapter, repo_path = storage
    # Create topic
    topic = Topic(id="123", name="test-topic")
    await storage_adapter.create_topic(topic)
    
    # Create message with attachment
    attachment = Attachment(
        id="photo_123",
        type="image/jpeg",
        filename="test.jpg",
        data=b"test data"
    )
    message = Message(
        content="Test message with photo",
        source="test_user",
        timestamp=datetime.utcnow(),
        attachments=[attachment]
    )
    
    await storage_adapter.save_message("123", message)
    
    # Verify attachment file
    attachment_path = repo_path / "topics" / "test-topic" / "media" / "jpg" / "test.jpg"
    assert attachment_path.exists(), "Attachment file should exist"
    with open(attachment_path, 'rb') as f:
        data = f.read()
        assert data == b"test data", "Attachment data should match"
    
    # Verify git status
    repo = Repo(repo_path)
    assert not repo.is_dirty(), "Repository should be clean after commit"
    
    # Verify metadata
    verify_metadata_yaml(repo_path, "123", "test-topic")

@pytest.mark.asyncio
async def test_multiple_topics_live(storage):
    """Test handling multiple topics with real git repo"""
    storage_adapter, repo_path = storage
    
    # Create multiple topics
    topics = [
        Topic(id="123", name="topic-1"),
        Topic(id="456", name="topic-2"),
        Topic(id="789", name="topic-3")
    ]
    
    for topic in topics:
        await storage_adapter.create_topic(topic)
        
        # Save a message to each topic
        message = Message(
            content=f"Test message for {topic.name}",
            source="test_user",
            timestamp=datetime.utcnow()
        )
        await storage_adapter.save_message(topic.id, message)
        
        # Verify topic structure
        topic_path = repo_path / "topics" / topic.name
        assert topic_path.exists(), f"Topic directory {topic.name} should exist"
        assert (topic_path / "messages.jsonl").exists(), f"Messages file for {topic.name} should exist"
        
        # Verify metadata for each topic
        verify_metadata_yaml(repo_path, topic.id, topic.name)
    
    # Verify git status
    repo = Repo(repo_path)
    assert not repo.is_dirty(), "Repository should be clean after all operations" 