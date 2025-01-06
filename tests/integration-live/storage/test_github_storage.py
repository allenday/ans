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
def github_token() -> str:
    """Get GitHub token from environment"""
    token = os.getenv('GITHUB_TOKEN')
    assert token, "GITHUB_TOKEN environment variable must be set"
    return token

@pytest.fixture
def github_repo() -> str:
    """Get GitHub test repo from environment"""
    repo = os.getenv('GITHUB_TEST_REPO')
    assert repo, "GITHUB_TEST_REPO environment variable must be set"
    return repo

@pytest_asyncio.fixture
async def github_storage(tmp_path, github_repo, github_token):
    """Provides GitStorageAdapter configured with GitHub remote"""
    adapter = GitStorageAdapter(base_path=tmp_path)
    user = User(id="test_user", name="Test User")
    await adapter.init_storage(user)
    
    # Configure git user for commits
    repo = Repo(adapter.repo_path)
    with repo.config_writer() as cw:
        cw.set_value('user', 'name', 'Integration Test')
        cw.set_value('user', 'email', 'test@example.com')
    
    # Set up remote with authentication
    remote_url = github_repo.replace('https://', f'https://{github_token}@')
    adapter.add_remote('origin', remote_url)
    
    try:
        # Try to pull existing content
        await adapter.sync()
    except:
        # Force push clean state
        repo.git.push('-u', 'origin', 'main', '--force')
    
    yield adapter
    
    # Cleanup
    try:
        shutil.rmtree(tmp_path)
    except:
        pass

@pytest.mark.slow
@pytest.mark.asyncio
async def test_github_push(github_storage, caplog, test_log_level):
    """Test pushing changes to GitHub"""
    caplog.set_level(test_log_level)
    adapter = await github_storage
    topic = Topic(
        id="live_test_topic", 
        name="Live Test Topic",
        metadata={
            'source': 'telegram',
            'chat_id': '123456',
            'chat_title': 'chronicler-dev',
            'description': 'Test topic'
        }
    )
    await adapter.create_topic(topic, ignore_exists=True)
    
    # Add test message
    message = Message(
        content="Test message from live integration",
        metadata={
            'source': 'telegram',
            'chat_id': '123456',
            'chat_title': 'chronicler-dev'
        },
        source="test",
        timestamp=datetime.utcnow()
    )
    await adapter.save_message(topic.id, message)
    
    # Add test attachment
    test_content = b"Test attachment content"
    attachment = Attachment(
        id="test_attachment",
        type="text/plain",
        filename="test.txt",
        data=test_content
    )
    await adapter.save_attachment(topic.id, "test_message", attachment)
    
    # Push changes
    await adapter.sync()
    
    # Verify through clone
    clone_path = Path(tempfile.mkdtemp())
    try:
        cloned_repo = Repo.clone_from(adapter._repo.remotes.origin.url, clone_path)
        
        # Check message content
        cloned_messages = clone_path / "telegram" / "123456" / topic.id / GitStorageAdapter.MESSAGES_FILE
        assert cloned_messages.exists(), "Messages file not found in clone"
        content = cloned_messages.read_text()
        assert "Test message from live integration" in content
        
        # Check attachment
        cloned_attachment = clone_path / "telegram" / "123456" / topic.id / "attachments" / "txt" / "test_attachment.txt"
        assert cloned_attachment.exists(), "Attachment file not found in clone"
        assert cloned_attachment.read_bytes() == test_content, "Attachment content mismatch"
        
        # Check metadata
        metadata_file = clone_path / "metadata.yaml"
        assert metadata_file.exists()
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
        assert topic.id in metadata['sources']['telegram']['groups']['123456']['topics']
        assert metadata['sources']['telegram']['groups']['123456']['topics'][topic.id]['name'] == topic.name
    finally:
        shutil.rmtree(clone_path)
