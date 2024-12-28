import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch
import frontmatter

from chronicler.storage import GitStorage

@pytest.fixture
def temp_dir():
    """Provides a temporary directory that's cleaned up after tests"""
    tmp_path = Path(tempfile.mkdtemp())
    yield tmp_path
    shutil.rmtree(tmp_path)

@pytest.fixture
def storage(temp_dir):
    """Provides a GitStorage instance with mocked git operations"""
    with patch('chronicler.storage.Repo') as mock_repo_class:
        # Create a mock repo instance
        mock_repo = Mock()
        mock_repo_class.init.return_value = mock_repo
        
        # Create the storage instance
        storage = GitStorage(base_path=temp_dir, user_id="test_user")
        
        # Pre-initialize with mock repo
        storage._repo = mock_repo
        
        yield storage

def test_create_topic(storage):
    """Test creating a new topic directory structure"""
    storage.init_user_repo()  # This won't create a new repo since we pre-initialized
    topic_id = "topic_123"
    
    # Reset mock counts after init
    storage._repo.index.add.reset_mock()
    storage._repo.index.commit.reset_mock()
    
    storage.create_topic(topic_id, "Test Topic")
    
    topic_path = storage.repo_path / "topics" / topic_id
    assert topic_path.exists()
    assert (topic_path / "messages.md").exists()
    assert (topic_path / "media").exists()
    
    # Verify commit was made
    storage._repo.index.add.assert_called_once_with([f'topics/{topic_id}', 'metadata.yaml'])
    storage._repo.index.commit.assert_called_once_with("Created topic: Test Topic")

def test_record_message(storage):
    """Test recording a message to a topic"""
    storage.init_user_repo()
    topic_id = "topic_123"
    storage.create_topic(topic_id, "Test Topic")
    
    # Reset mock counts after setup
    storage._repo.index.add.reset_mock()
    storage._repo.index.commit.reset_mock()
    
    message = {
        "text": "Test message",
        "timestamp": "2024-03-20T12:00:00Z",
        "sender": "user123"
    }
    
    storage.record_message(topic_id, message)
    
    # Check message was written
    messages_file = storage.repo_path / "topics" / topic_id / "messages.md"
    content = messages_file.read_text()
    assert "Test message" in content
    
    # Verify commit was made
    storage._repo.index.add.assert_called_once_with([f'topics/{topic_id}/messages.md'])
    storage._repo.index.commit.assert_called_once_with("Added message to topic: Test Topic") 

def test_record_message_format(storage):
    """Test that messages are recorded with correct frontmatter format"""
    storage.init_user_repo()
    topic_id = "topic_123"
    storage.create_topic(topic_id, "Test Topic")
    
    # Reset mock counts after setup
    storage._repo.index.add.reset_mock()
    storage._repo.index.commit.reset_mock()
    
    message = {
        "text": "Test message",
        "timestamp": "2024-03-20T12:00:00Z",
        "sender": "user123"
    }
    
    storage.record_message(topic_id, message)
    
    # Check message format
    messages_file = storage.repo_path / "topics" / topic_id / "messages.md"
    content = messages_file.read_text()
    
    # Parse the frontmatter
    post = frontmatter.loads(content)
    assert post.content.strip() == "Test message"
    assert post.metadata['timestamp'].isoformat() == "2024-03-20T12:00:00+00:00"
    assert post.metadata['sender'] == "user123"
    assert post.metadata['type'] == "message"
    assert 'message_id' in post.metadata
    
    # Verify commit was made
    storage._repo.index.add.assert_called_once_with([f'topics/{topic_id}/messages.md'])
    storage._repo.index.commit.assert_called_once_with("Added message to topic: Test Topic") 