import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from chronicler.storage import GitStorage
from git import Repo
import tempfile
import shutil
import yaml

# Load environment variables
load_dotenv()

@pytest.fixture
def github_repo():
    """Provides GitHub repository URL from environment"""
    repo_url = os.getenv("GITHUB_TEST_REPO")
    if not repo_url:
        pytest.skip("GITHUB_TEST_REPO not configured")
    return repo_url

@pytest.fixture
def github_storage(tmp_path, github_repo):
    """Provides GitStorage configured with GitHub remote"""
    storage = GitStorage(base_path=tmp_path, user_id="test_user")
    storage.init_user_repo()
    
    # Configure git user for commits
    repo = Repo(storage.repo_path)
    with repo.config_writer() as cw:
        cw.set_value('user', 'name', 'Integration Test')
        cw.set_value('user', 'email', 'test@example.com')
    
    # Set up remote and sync
    storage.add_remote('origin', github_repo)
    
    try:
        # Try to pull existing content
        repo.git.pull('origin', 'main', '--allow-unrelated-histories')
    except:
        # If pull fails (e.g., empty repo), force push our initial structure
        repo.git.push('-u', 'origin', 'main', '--force')
    
    return storage

def test_github_push(github_storage):
    """Test pushing changes to GitHub"""
    # Create and push changes
    topic_id = "live_test_topic"
    github_storage.create_topic(topic_id, "Live Test Topic")
    
    # Add a test message
    message = {
        "text": "Test message from live integration",
        "timestamp": "2024-03-20T12:00:00Z",
        "sender": "test_user"
    }
    github_storage.record_message(topic_id, message)
    
    # Push changes
    github_storage.push()
    
    # Debug: Check local content
    messages_file = github_storage.repo_path / "topics" / topic_id / "messages.md"
    print(f"\nLocal messages content:\n{messages_file.read_text()}")
    
    # Clone and verify
    clone_path = Path(tempfile.mkdtemp())
    try:
        cloned_repo = Repo.clone_from(github_storage._repo.remotes.origin.url, clone_path)
        
        # Check cloned content
        cloned_messages = clone_path / "topics" / topic_id / "messages.md"
        print(f"\nCloned messages content:\n{cloned_messages.read_text()}")
        
        assert cloned_messages.exists(), "Messages file not found in clone"
        content = cloned_messages.read_text()
        assert "Test message from live integration" in content, "Message content not found"
        
        # Check metadata
        metadata_file = clone_path / "metadata.yaml"
        assert metadata_file.exists(), "Metadata file not found"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)
        assert topic_id in metadata['topics'], "Topic not found in metadata"
    finally:
        shutil.rmtree(clone_path)
