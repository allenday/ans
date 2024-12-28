import pytest
from pathlib import Path
import tempfile
import shutil
from git import Repo

from chronicler.storage import GitStorage

@pytest.fixture
def temp_dir():
    """Provides a temporary directory that's cleaned up after tests"""
    tmp_path = Path(tempfile.mkdtemp())
    yield tmp_path
    shutil.rmtree(tmp_path)

@pytest.fixture
def storage(temp_dir):
    """Provides a GitStorage instance configured with a temp directory"""
    return GitStorage(base_path=temp_dir, user_id="test_user")

def test_init_user_repo(storage, temp_dir):
    """Test that we can initialize a new user repository with correct structure"""
    storage.init_user_repo()
    
    # Check that repo was created
    repo_path = temp_dir / "test_user_journal"
    assert repo_path.exists()
    assert (repo_path / ".git").exists()
    
    # Check basic structure
    assert (repo_path / "topics").exists()
    assert (repo_path / "metadata.yaml").exists()
    
    # Verify it's a valid git repo
    repo = Repo(repo_path)
    assert not repo.bare
    assert repo.active_branch.name == "main"

def test_git_operations(storage, temp_dir):
    """Test full git workflow with actual commits"""
    storage.init_user_repo()
    topic_id = "topic_123"
    
    # Create topic and verify commit
    storage.create_topic(topic_id, "Test Topic")
    repo = Repo(temp_dir / "test_user_journal")
    assert "Created topic: Test Topic" in repo.head.commit.message
    
    # Add message and verify commit
    message = {
        "text": "Test message",
        "timestamp": "2024-03-20T12:00:00Z",
        "sender": "user123"
    }
    storage.record_message(topic_id, message)
    assert "Added message to topic: Test Topic" in repo.head.commit.message 