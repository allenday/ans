import pytest
import pytest_asyncio
import os
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, PropertyMock, MagicMock
import yaml
from git import Repo
from git.exc import InvalidGitRepositoryError
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
    # Clean up any existing test data
    test_path = tmp_path / "test_user_journal"
    if test_path.exists():
        logger.info(f"Cleaning up existing test data at {test_path}")
        shutil.rmtree(test_path)
    
    # Create the repository directory
    repo_path = tmp_path / "test_user_journal"
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Create mock repo
    mock_repo = Mock(spec=Repo)
    mock_repo.index = Mock()
    mock_repo.index.add = Mock()
    mock_repo.index.commit = Mock()
    mock_repo.remotes = {}
    mock_repo.git = Mock()
    mock_repo.working_dir = str(repo_path)
    
    # Mock git operations
    with patch('git.Repo.init', return_value=mock_repo) as mock_init, \
         patch('git.Repo', return_value=mock_repo) as mock_repo_class:
        
        # Create storage adapter
        storage = GitStorageAdapter(tmp_path)
        user = User(id="test_user", name="Test User")
        await storage.init_storage(user)
        
        # Verify initial metadata
        verify_metadata_yaml(repo_path)
        
        # Reset mock calls from initialization
        mock_repo.reset_mock()
        return storage, mock_repo, repo_path

@pytest.mark.asyncio
async def test_topic_creation_with_git(storage):
    """Test that topic creation properly interacts with git"""
    storage_adapter, mock_repo, repo_path = storage
    topic = Topic(
        id="123456789",
        name="Test Topic",
        metadata={
            "source": "telegram",
            "chat_id": "987654321",
            "chat_title": "Test Group"
        }
    )
    await storage_adapter.create_topic(topic)
    
    # Verify git operations
    mock_repo.index.add.assert_any_call(['telegram'])
    mock_repo.index.add.assert_any_call(['telegram/987654321'])
    mock_repo.index.add.assert_any_call(['telegram/987654321/123456789'])
    mock_repo.index.add.assert_any_call(['metadata.yaml'])
    mock_repo.index.commit.assert_called_with("Created topic: Test Topic")
    
    # Verify metadata structure
    metadata_path = repo_path / "metadata.yaml"
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
async def test_message_save_with_git(storage):
    """Test that message saving properly interacts with git"""
    storage_adapter, mock_repo, repo_path = storage
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
    await storage_adapter.create_topic(topic)
    
    # Reset mock calls from topic creation
    mock_repo.reset_mock()
    
    # Create and save message
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
    await storage_adapter.save_message("123456789", message)
    
    # Verify git operations
    mock_repo.index.add.assert_called_with(['telegram/987654321/123456789/messages.jsonl'])
    mock_repo.index.commit.assert_called_with("Added message to topic: Test Topic")

@pytest.mark.asyncio
async def test_attachment_save_with_git(storage):
    """Test that attachment saving properly interacts with git"""
    storage_adapter, mock_repo, repo_path = storage
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
    await storage_adapter.create_topic(topic)
    
    # Reset mock calls from topic creation
    mock_repo.reset_mock()
    
    # Create message with attachment
    attachment = Attachment(
        id="AgACAgEAAx0CR2WwagADHGR_Y_h8zG4HMc5SdngsvciqrEgHowACGq0xG_2PiEdml3NAynBCrgEAAwIAA20AAzYE",
        type="image/jpeg",
        filename="test.jpg",
        data=b"test data"
    )
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
    
    await storage_adapter.save_message("123456789", message)
    
    # Verify git operations for both message and attachment
    mock_repo.index.add.assert_any_call([f'telegram/987654321/123456789/attachments/jpg/{attachment.id}.jpg'])
    mock_repo.index.add.assert_any_call(['telegram/987654321/123456789/messages.jsonl'])
    mock_repo.index.commit.assert_called_with("Added message to topic: Test Topic")
    
    # Verify message metadata
    messages_file = repo_path / "telegram" / "987654321" / "123456789" / "messages.jsonl"
    with open(messages_file) as f:
        message_data = json.loads(f.read().strip())
        assert message_data["attachments"][0]["id"] == attachment.id
        assert message_data["attachments"][0]["original_name"] == "test.jpg"

@pytest.mark.asyncio
async def test_github_config_with_git(storage):
    """Test GitHub configuration with git operations"""
    storage_adapter, mock_repo, repo_path = storage
    token = "test_token"
    repo = "test/repo"
    
    # Mock remote operations
    mock_remote = Mock()
    mock_repo.remotes = {'origin': mock_remote}
    mock_repo.create_remote = Mock(return_value=mock_remote)
    mock_repo.delete_remote = Mock()
    
    # Configure GitHub
    await storage_adapter.set_github_config(token, repo)
    
    # Verify remote operations
    expected_url = f"https://{token}@github.com/{repo}.git"
    mock_repo.delete_remote.assert_called_with('origin')
    mock_repo.create_remote.assert_called_with('origin', expected_url)
    mock_repo.index.add.assert_called_with(['metadata.yaml'])
    mock_repo.index.commit.assert_called_with("Updated GitHub configuration")
    
    # Verify metadata still valid
    verify_metadata_yaml(repo_path)

@pytest.mark.asyncio
async def test_sync_with_git(storage):
    """Test sync operation with git"""
    storage_adapter, mock_repo, repo_path = storage
    # Mock remote operations
    mock_remote = Mock()
    mock_repo.remotes = {'origin': mock_remote}
    mock_repo.git.push = Mock()
    
    # Perform sync
    await storage_adapter.sync()
    
    # Verify git operations
    mock_repo.git.push.assert_called_with('-f', 'origin', 'main')
    
    # Verify metadata still valid
    verify_metadata_yaml(repo_path) 