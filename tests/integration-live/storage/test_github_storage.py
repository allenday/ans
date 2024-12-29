import os
import pytest
import pytest_asyncio
from pathlib import Path
from dotenv import load_dotenv
from chronicler.storage.interface import User, Topic, Message, Attachment
from chronicler.storage.git import GitStorageAdapter
from git import Repo
import tempfile
import shutil
import yaml
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Mark all tests in this file as live integration tests
pytestmark = [
    pytest.mark.live,
    pytest.mark.integration,
    pytest.mark.codex  # These are storage/codex tests, not scribe tests
]

@pytest.fixture
def github_repo():
    """Provides GitHub repository URL from environment"""
    repo_url = os.getenv("GITHUB_TEST_REPO")
    if not repo_url:
        pytest.skip("GITHUB_TEST_REPO environment variable not set. Source .env file to run live tests.")
    return repo_url

@pytest_asyncio.fixture
async def github_storage(tmp_path, github_repo):
    """Provides GitStorageAdapter configured with GitHub remote"""
    adapter = GitStorageAdapter(base_path=tmp_path)
    user = User(id="test_user", name="Test User")
    await adapter.init_storage(user)
    
    # Configure git user for commits
    repo = Repo(adapter.repo_path)
    with repo.config_writer() as cw:
        cw.set_value('user', 'name', 'Integration Test')
        cw.set_value('user', 'email', 'test@example.com')
    
    # Set up remote and sync
    adapter.add_remote('origin', github_repo)
    
    try:
        # Try to pull existing content
        await adapter.sync()
    except:
        # Force push clean state
        repo.git.push('-u', 'origin', 'main', '--force')
    
    return adapter

@pytest.mark.slow
@pytest.mark.asyncio
async def test_github_push(github_storage, caplog, test_log_level):
    """Test pushing changes to GitHub"""
    caplog.set_level(test_log_level)
    adapter = await github_storage
    topic = Topic(id="live_test_topic", name="Live Test Topic")
    await adapter.create_topic(topic, ignore_exists=True)
    
    # Add test message
    message = Message(
        content="Test message from live integration",
        metadata={},
        source="test",
        timestamp=datetime.utcnow()
    )
    await adapter.save_message(topic.id, message)
    
    # Push changes
    await adapter.sync()
    
    # Verify through clone
    clone_path = Path(tempfile.mkdtemp())
    try:
        cloned_repo = Repo.clone_from(adapter._repo.remotes.origin.url, clone_path)
        
        # Check content
        cloned_messages = clone_path / "topics" / topic.id / GitStorageAdapter.MESSAGES_FILE
        assert cloned_messages.exists(), "Messages file not found in clone"
        content = cloned_messages.read_text()
        assert "Test message from live integration" in content
        
        # Check metadata
        metadata_file = clone_path / "metadata.yaml"
        assert metadata_file.exists()
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
        assert topic.id in metadata['topics']
    finally:
        shutil.rmtree(clone_path)
