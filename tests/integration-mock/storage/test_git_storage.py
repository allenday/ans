import pytest
from pathlib import Path
import tempfile
import shutil
from git import Repo
import yaml
from chronicler.storage import GitStorage

@pytest.fixture
def temp_dir():
    """Provides a temporary directory that's cleaned up after tests"""
    tmp_path = Path(tempfile.mkdtemp())
    yield tmp_path
    shutil.rmtree(tmp_path)

@pytest.fixture
def bare_repo():
    """Creates a bare repo that acts as a remote with initial structure"""
    tmp_path = Path(tempfile.mkdtemp())
    bare_repo = Repo.init(tmp_path / "remote.git", bare=True, initial_branch='main')
    
    # Create a temporary clone to set up initial structure
    working_dir = tmp_path / "setup"
    setup_repo = Repo.clone_from(bare_repo.working_dir, working_dir)
    
    # Create initial structure
    (working_dir / ".gitkeep").touch()
    setup_repo.index.add([".gitkeep"])
    setup_repo.index.commit("Initial commit")
    setup_repo.git.push('origin', 'main')
    
    yield bare_repo
    shutil.rmtree(tmp_path)

@pytest.fixture
def storage_with_remote(temp_dir, bare_repo):
    """Provides a GitStorage instance configured with a remote"""
    # Initialize storage first (this creates the directory)
    storage = GitStorage(base_path=temp_dir, user_id="test_user")
    storage.init_user_repo()
    
    # Set up git repo with remote
    repo = Repo(storage.repo_path)
    repo.create_remote('origin', bare_repo.working_dir)
    
    # Configure git to use rebase strategy
    with repo.config_writer() as cw:
        cw.set_value('pull', 'rebase', 'true')
    
    # Pull from remote to sync histories
    repo.git.pull('origin', 'main')
    
    return storage

def test_push_to_remote(storage_with_remote):
    """Test that changes are pushed to remote"""
    topic_id = "topic_123"
    storage_with_remote.create_topic(topic_id, "Test Topic")
    
    message = {
        "text": "Test message",
        "timestamp": "2024-03-20T12:00:00Z",
        "sender": "user123"
    }
    storage_with_remote.record_message(topic_id, message)
    
    # Push changes to remote
    storage_with_remote.push()
    
    # Clone the bare repo to verify contents
    clone_path = Path(tempfile.mkdtemp())
    cloned_repo = Repo.clone_from(storage_with_remote._repo.remotes.origin.url, clone_path)
    
    try:
        # Check that files exist in clone
        messages_file = clone_path / "topics" / topic_id / "messages.md"
        assert messages_file.exists(), "Messages file not found in cloned repo"
        
        # Verify content
        content = messages_file.read_text()
        assert "Test message" in content, "Message content not found in cloned repo"
        
        # Check metadata
        metadata_file = clone_path / "metadata.yaml"
        assert metadata_file.exists(), "Metadata file not found in cloned repo"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
        assert topic_id in metadata['topics'], "Topic not found in metadata"
    finally:
        # Cleanup
        shutil.rmtree(clone_path)

def test_remote_operations(storage_with_remote):
    """Test various remote operations"""
    # Test that remote is properly configured
    assert 'origin' in [r.name for r in storage_with_remote._repo.remotes]
    
    # Test basic push operation
    storage_with_remote.create_topic("test_topic", "Test Topic")
    storage_with_remote.push()
    
    # Verify remote has our changes
    clone_path = Path(tempfile.mkdtemp())
    try:
        cloned_repo = Repo.clone_from(storage_with_remote._repo.remotes.origin.url, clone_path)
        assert (clone_path / "topics" / "test_topic").exists()
    finally:
        shutil.rmtree(clone_path) 