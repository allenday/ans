"""Tests for git storage adapter."""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import json
from datetime import datetime
from git import Repo, InvalidGitRepositoryError

from chronicler.storage.git import GitStorageAdapter, EntityType

@pytest.fixture
def base_path(tmp_path):
    """Create a temporary base path for testing."""
    path = tmp_path / "test_storage"
    path.mkdir(parents=True)
    return path

@pytest.fixture
def mock_repo(base_path):
    """Mock git repository."""
    mock = MagicMock()
    mock.head.is_valid.return_value = True  # Changed to True since we want to simulate an initialized repo
    mock.git = MagicMock()
    mock.index = MagicMock()
    type(mock).working_dir = PropertyMock(return_value=str(base_path))
    
    # Mock heads and active_branch
    mock_main_branch = MagicMock()
    mock_main_branch.name = 'main'
    mock.heads = {'main': mock_main_branch}
    type(mock).active_branch = PropertyMock(return_value=mock_main_branch)
    
    # Mock commits
    mock_commit = MagicMock()
    mock.iter_commits.return_value = [mock_commit]
    
    return mock

@pytest.fixture
def git_adapter(base_path, mock_repo):
    """Create a GitStorageAdapter instance with mocked Git operations."""
    with patch('git.Repo', return_value=mock_repo) as mock_repo_class:
        mock_repo_class.init = MagicMock(return_value=mock_repo)
        adapter = GitStorageAdapter(base_path)
        adapter.repo = mock_repo  # Ensure we use our mock
        return adapter

def test_initialization(base_path, git_adapter):
    """Test initialization of GitStorageAdapter."""
    # Verify that repo is initialized
    assert git_adapter.repo is not None
    assert git_adapter.repo.working_dir == str(base_path)
    
    # Verify that main branch exists and is the current branch
    assert 'main' in git_adapter.repo.heads
    assert git_adapter.repo.active_branch.name == 'main'
    
    # Verify that initial commit exists
    assert git_adapter.repo.head.is_valid()
    assert len(list(git_adapter.repo.iter_commits())) > 0
    
    # Verify .gitkeep exists
    assert (base_path / '.gitkeep').exists()

def test_init_storage(git_adapter):
    """Test initializing storage for a source."""
    source = "telegram"
    git_adapter.init_storage(source)
    
    # Verify source structure was created
    source_path = git_adapter.base_path / source
    assert source_path.exists()
    assert (source_path / "metadata.json").exists()
    assert (source_path / "users").exists()
    assert (source_path / "groups").exists()
    assert (source_path / "supergroups").exists()
    
    # Verify metadata content
    with (source_path / "metadata.json").open() as f:
        metadata = json.load(f)
        assert metadata["source"] == source
        assert "entities" in metadata
        assert all(k in metadata["entities"] for k in ["users", "groups", "supergroups"])

def test_create_user(git_adapter):
    """Test creating a user entity."""
    source = "telegram"
    user_id = "123456789"
    metadata = {
        "username": "testuser",
        "display_name": "Test User"
    }
    
    # Initialize storage first
    git_adapter.init_storage(source)
    
    # Create user
    git_adapter.create_entity(source, EntityType.USER, user_id, metadata)
    
    # Verify user was created
    user_path = git_adapter.base_path / source / "users" / user_id
    assert user_path.exists()
    assert (user_path / "messages.jsonl").exists()
    assert (user_path / "attachments").exists()
    
    # Verify metadata was updated
    with (git_adapter.base_path / source / "metadata.json").open() as f:
        source_meta = json.load(f)
        assert user_id in source_meta["entities"]["users"]
        assert source_meta["entities"]["users"][user_id]["username"] == "testuser"

def test_create_supergroup_with_topic(git_adapter):
    """Test creating a supergroup and adding a topic."""
    source = "telegram"
    group_id = "-100123456789"
    topic_id = "42"
    group_metadata = {
        "title": "Test Group",
        "type": "supergroup"
    }
    topic_metadata = {
        "name": "Test Topic",
        "creator_id": "123456789"
    }
    
    # Initialize storage and create supergroup
    git_adapter.init_storage(source)
    git_adapter.create_entity(source, EntityType.SUPERGROUP, group_id, group_metadata)
    
    # Create topic
    git_adapter.create_topic(source, group_id, topic_id, topic_metadata)
    
    # Verify supergroup and topic structure
    group_path = git_adapter.base_path / source / "supergroups" / group_id
    topic_path = group_path / "topics" / topic_id
    assert group_path.exists()
    assert (group_path / "messages.jsonl").exists()
    assert (group_path / "attachments").exists()
    assert (group_path / "topics").exists()
    assert topic_path.exists()
    assert (topic_path / "messages.jsonl").exists()
    assert (topic_path / "attachments").exists()
    
    # Verify metadata was updated
    with (git_adapter.base_path / source / "metadata.json").open() as f:
        source_meta = json.load(f)
        group_data = source_meta["entities"]["supergroups"][group_id]
        assert group_data["title"] == "Test Group"
        assert topic_id in group_data["topics"]
        assert group_data["topics"][topic_id]["name"] == "Test Topic"

def test_sync_no_remote(git_adapter):
    """Test sync fails when no remote is configured."""
    source = "telegram"
    git_adapter.init_storage(source)
    
    # Mock no remotes
    git_adapter.repo.remotes.__iter__.return_value = iter([])
    
    with pytest.raises(RuntimeError, match="No remotes configured"):
        git_adapter.sync(source)

def test_sync_with_remote(git_adapter):
    """Test sync succeeds after configuring remote."""
    source = "telegram"
    git_adapter.init_storage(source)
    
    # Mock remote
    mock_remote = MagicMock()
    git_adapter.repo.remotes.__iter__.return_value = iter([mock_remote])
    git_adapter.repo.remotes.__getitem__.return_value = mock_remote
    git_adapter.repo.head.tracking_branch.return_value = None  # No tracking branch yet
    
    # Configure remote
    git_adapter.set_github_config("test_token", "test/repo")
    
    # Should not raise
    git_adapter.sync(source)
    
    # Verify remote operations
    mock_remote.push.assert_called_once()

def test_set_github_config(git_adapter):
    """Test setting GitHub configuration."""
    # Mock no existing remote
    git_adapter.repo.remotes.__contains__.return_value = False
    
    git_adapter.set_github_config("test_token", "test/repo")
    
    # Verify remote was created
    git_adapter.repo.create_remote.assert_called_once_with(
        'origin',
        'https://test_token@github.com/test/repo'
    )

def test_set_github_config_existing_remote(git_adapter):
    """Test setting GitHub config with existing remote."""
    # Mock existing remote
    git_adapter.repo.remotes.__contains__.return_value = True
    mock_remote = MagicMock()
    git_adapter.repo.remotes.__getitem__.return_value = mock_remote
    
    git_adapter.set_github_config("test_token", "test/repo")
    
    # Verify old remote was deleted and new one created
    git_adapter.repo.delete_remote.assert_called_once_with('origin')
    git_adapter.repo.create_remote.assert_called_once_with(
        'origin',
        'https://test_token@github.com/test/repo'
    )

def test_save_message_to_user(git_adapter):
    """Test saving a message to a user."""
    source = "telegram"
    user_id = "123456789"
    message = {
        "id": "msg_1",
        "content": "Test message",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"reply_to": None}
    }
    
    # Initialize storage and create user
    git_adapter.init_storage(source)
    git_adapter.create_entity(source, EntityType.USER, user_id, {"username": "testuser"})
    
    # Save message
    git_adapter.save_message(source, EntityType.USER, user_id, message)
    
    # Verify message was saved
    messages_file = git_adapter.base_path / source / "users" / user_id / "messages.jsonl"
    with messages_file.open() as f:
        saved_message = json.loads(f.read().strip())
        assert saved_message["content"] == "Test message"
        assert saved_message["id"] == "msg_1"

def test_save_message_to_topic(git_adapter):
    """Test saving a message to a topic in a supergroup."""
    source = "telegram"
    group_id = "-100123456789"
    topic_id = "42"
    message = {
        "id": "msg_1",
        "content": "Test topic message",
        "timestamp": datetime.now().isoformat(),
        "metadata": {"topic_id": topic_id}
    }
    
    # Initialize storage and create supergroup with topic
    git_adapter.init_storage(source)
    git_adapter.create_entity(source, EntityType.SUPERGROUP, group_id, {"title": "Test Group"})
    git_adapter.create_topic(source, group_id, topic_id, {"name": "Test Topic"})
    
    # Save message
    git_adapter.save_message(source, EntityType.SUPERGROUP, group_id, message, topic_id)
    
    # Verify message was saved
    messages_file = git_adapter.base_path / source / "supergroups" / group_id / "topics" / topic_id / "messages.jsonl"
    with messages_file.open() as f:
        saved_message = json.loads(f.read().strip())
        assert saved_message["content"] == "Test topic message"
        assert saved_message["id"] == "msg_1"

def test_save_attachment(git_adapter, tmp_path):
    """Test saving an attachment to a user."""
    source = "telegram"
    user_id = "123456789"
    file_path = tmp_path / "test.txt"
    attachment_name = "test.txt"
    
    # Create test file
    with file_path.open("w") as f:
        f.write("Test content")
    
    # Initialize storage and create user
    git_adapter.init_storage(source)
    git_adapter.create_entity(source, EntityType.USER, user_id, {"username": "testuser"})
    
    # Save attachment
    git_adapter.save_attachment(source, EntityType.USER, user_id, file_path, attachment_name)
    
    # Verify attachment was saved
    attachment_path = git_adapter.base_path / source / "users" / user_id / "attachments" / attachment_name
    assert attachment_path.exists()
    with attachment_path.open() as f:
        assert f.read() == "Test content"

def test_save_attachment_to_topic(git_adapter, tmp_path):
    """Test saving an attachment to a topic."""
    source = "telegram"
    group_id = "-100123456789"
    topic_id = "42"
    file_path = tmp_path / "test.txt"
    attachment_name = "test.txt"
    
    # Create test file
    with file_path.open("w") as f:
        f.write("Test content")
    
    # Initialize storage and create supergroup with topic
    git_adapter.init_storage(source)
    git_adapter.create_entity(source, EntityType.SUPERGROUP, group_id, {"title": "Test Group"})
    git_adapter.create_topic(source, group_id, topic_id, {"name": "Test Topic"})
    
    # Save attachment
    git_adapter.save_attachment(source, EntityType.SUPERGROUP, group_id, file_path, attachment_name, topic_id)
    
    # Verify attachment was saved
    attachment_path = git_adapter.base_path / source / "supergroups" / group_id / "topics" / topic_id / "attachments" / attachment_name
    assert attachment_path.exists()
    with attachment_path.open() as f:
        assert f.read() == "Test content"