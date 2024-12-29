import pytest
from pathlib import Path
import tempfile
import shutil
from git import Repo
import yaml
from chronicler.storage import GitStorageAdapter
from chronicler.storage.interface import User, Topic, Message
from datetime import datetime

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
async def storage_with_remote(temp_dir, bare_repo):
    """Provides a GitStorageAdapter instance configured with a remote"""
    # Initialize storage first (this creates the directory)
    adapter = GitStorageAdapter(base_path=temp_dir)
    user = User(id="test_user", name="Test User")
    await adapter.init_storage(user)
    
    # Set up git repo with remote
    repo = Repo(adapter.repo_path)
    repo.create_remote('origin', bare_repo.working_dir)
    
    # Configure git to use rebase strategy
    with repo.config_writer() as cw:
        cw.set_value('pull', 'rebase', 'true')
    
    # Pull from remote to sync histories
    repo.git.pull('origin', 'main')
    
    return adapter

@pytest.mark.asyncio
async def test_push_to_remote(storage_with_remote):
    """Test that changes are pushed to remote"""
    adapter = await storage_with_remote
    topic = Topic(id="topic_123", name="Test Topic")
    await adapter.create_topic(topic)
    
    message = Message(
        content="Test message",
        metadata={"sender": "user123"},
        source="test",
        timestamp=datetime.fromisoformat("2024-03-20T12:00:00+00:00")
    )
    await adapter.save_message(topic.id, message)
    
    # Push changes to remote
    await adapter.sync()
    
    # Clone the bare repo to verify contents
    clone_path = Path(tempfile.mkdtemp())
    cloned_repo = Repo.clone_from(adapter._repo.remotes.origin.url, clone_path)
    
    try:
        # Check that files exist in clone
        cloned_messages = clone_path / "topics" / topic.id / GitStorageAdapter.MESSAGES_FILE
        assert cloned_messages.exists(), "Messages file not found in cloned repo"
        
        # Verify content
        content = cloned_messages.read_text()
        assert "Test message" in content, "Message content not found in cloned repo"
        
        # Check metadata
        metadata_file = clone_path / "metadata.yaml"
        assert metadata_file.exists(), "Metadata file not found in cloned repo"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
        assert topic.id in metadata['topics'], "Topic not found in metadata"
    finally:
        # Cleanup
        shutil.rmtree(clone_path)

@pytest.mark.asyncio
async def test_remote_operations(storage_with_remote):
    """Test various remote operations"""
    adapter = await storage_with_remote
    # Test that remote is properly configured
    assert 'origin' in [r.name for r in adapter._repo.remotes]
    
    # Test basic push operation
    topic = Topic(id="test_topic", name="Test Topic")
    await adapter.create_topic(topic)
    await adapter.sync()
    
    # Verify remote has our changes
    clone_path = Path(tempfile.mkdtemp())
    try:
        cloned_repo = Repo.clone_from(adapter._repo.remotes.origin.url, clone_path)
        assert (clone_path / "topics" / "test_topic").exists()
    finally:
        shutil.rmtree(clone_path) 