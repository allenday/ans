import pytest
import pytest_asyncio
import os
import shutil
from pathlib import Path
from datetime import datetime
import yaml
from git import Repo
from chronicler.storage.interface import User, Topic, Message, Attachment
from chronicler.storage.git import GitStorageAdapter
import json
import logging

logger = logging.getLogger(__name__)

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
    # Clean up any existing test data
    test_path = tmp_path / "test_user_journal"
    if test_path.exists():
        logger.info(f"Cleaning up existing test data at {test_path}")
        shutil.rmtree(test_path)
    
    # Create storage adapter
    storage = GitStorageAdapter(tmp_path)
    user = User(id="test_user", name="Test User")
    await storage.init_storage(user)
    
    # Verify initial metadata
    repo_path = tmp_path / "test_user_journal"
    verify_metadata_yaml(repo_path)
    
    return storage, repo_path

@pytest.mark.integration
@pytest.mark.storage
@pytest.mark.asyncio
async def test_topic_creation_live(git_adapter_live):
    """Test creating a topic in a live Git repo"""
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
    
    await git_adapter_live.create_topic(topic)
    
    topic_dir = git_adapter_live.repo_path / "telegram" / "987654321" / "123456789"
    assert topic_dir.exists(), "Topic directory should exist"
    assert topic_dir.is_dir()
    assert (topic_dir / "messages.jsonl").exists(), "Messages file should exist"
    assert (topic_dir / "attachments").exists(), "Attachments directory should exist"

@pytest.mark.integration
@pytest.mark.storage
@pytest.mark.asyncio
async def test_message_save_live(git_adapter_live):
    """Test saving a message in a live Git repo"""
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
    await git_adapter_live.create_topic(topic)
    
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
    
    await git_adapter_live.save_message(topic.id, message)
    
    topic_dir = git_adapter_live.repo_path / "telegram" / "987654321" / "123456789"
    messages_file = topic_dir / "messages.jsonl"
    assert messages_file.exists(), "Messages file should exist"
    with open(messages_file) as f:
        lines = f.readlines()
        assert len(lines) == 1

@pytest.mark.integration
@pytest.mark.storage
@pytest.mark.asyncio
async def test_attachment_save_live(git_adapter_live):
    """Test saving an attachment in a live Git repo"""
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
    await git_adapter_live.create_topic(topic)
    
    attachment = Attachment(
        id="test_attachment",
        type="image/jpeg",
        filename="test.jpg",
        data=b"test content"
    )
    
    await git_adapter_live.save_attachment(topic.id, "msg_1", attachment)
    
    topic_dir = git_adapter_live.repo_path / "telegram" / "987654321" / "123456789"
    attachment_file = topic_dir / "attachments" / "jpg" / "test_attachment.jpg"
    assert attachment_file.exists(), "Attachment file should exist"

@pytest.mark.integration
@pytest.mark.storage
@pytest.mark.asyncio
async def test_multiple_topics_live(git_adapter_live):
    """Test creating multiple topics in a live Git repo"""
    topics = [
        Topic(
            id=f"12345678{i}",
            name=f"topic-{i}",
            metadata={
                "source": "telegram",
                "chat_id": "987654321",
                "chat_title": "Test Group",
                "description": f"Test topic {i}"
            }
        )
        for i in range(3)
    ]
    
    for topic in topics:
        await git_adapter_live.create_topic(topic)
        
        topic_dir = git_adapter_live.repo_path / "telegram" / "987654321" / topic.id
        assert topic_dir.exists(), f"Topic directory {topic.name} should exist"
        assert topic_dir.is_dir()
        assert (topic_dir / "messages.jsonl").exists()
        assert (topic_dir / "attachments").exists()

@pytest.mark.integration
@pytest.mark.storage
@pytest.mark.asyncio
async def test_github_push(git_adapter_live, tmp_path):
    """Test pushing changes to GitHub"""
    # Create a topic
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
    await git_adapter_live.create_topic(topic)
    
    # Add a message with attachment
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
    
    await git_adapter_live.save_message(topic.id, message)
    
    # Clone the repo to verify contents
    clone_path = tmp_path / "clone"
    repo = Repo.clone_from(git_adapter_live.repo_path, clone_path)
    
    topic_dir = clone_path / "telegram" / "987654321" / "123456789"
    assert (topic_dir / "messages.jsonl").exists(), "Messages file not found in clone"
    attachment_file = topic_dir / "attachments" / "jpg" / "test_attachment.jpg"
    assert attachment_file.exists(), "Attachment file not found in clone" 