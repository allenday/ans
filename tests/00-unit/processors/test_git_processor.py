"""Unit tests for GitProcessor."""
import os
from pathlib import Path
import pytest
from chronicler.processors.git_processor import GitProcessor, GitProcessingError
from unittest.mock import patch, MagicMock
import git

@pytest.fixture
def test_storage_path(tmp_path):
    """Create a temporary storage path with test files and initialize Git repo."""
    # Create message directory
    message_dir = tmp_path / "messages" / "2024-01-11"
    message_dir.mkdir(parents=True)
    message_path = message_dir / "message_123.json"
    message_path.write_text('{"test": "message"}')
    
    # Create media directory
    media_dir = tmp_path / "media" / "2024-01-11"
    media_dir.mkdir(parents=True)
    photo_path = media_dir / "photo_123.jpg"
    photo_path.write_text('test photo data')
    doc_path = media_dir / "document_456.pdf"
    doc_path.write_text('test document data')
    
    # Initialize Git repository
    repo = git.Repo.init(tmp_path)
    
    # Configure Git user for commits
    with repo.config_writer() as git_config:
        git_config.set_value('user', 'name', 'Test User')
        git_config.set_value('user', 'email', 'test@example.com')
    
    # Add and commit files
    repo.index.add([
        str(message_path.relative_to(tmp_path)),
        str(photo_path.relative_to(tmp_path)),
        str(doc_path.relative_to(tmp_path))
    ])
    repo.index.commit("Initial commit")
    
    # Create main branch at the initial commit
    repo.create_head('main')
    repo.heads.main.checkout()
    
    return tmp_path

class TestGitProcessor:
    """Test suite for GitProcessor."""
    
    def test_init_processor(self, test_storage_path):
        """Test GitProcessor initialization."""
        processor = GitProcessor(
            repo_url="https://github.com/test/repo.git",
            branch="main", 
            username="testuser",
            access_token="testtoken",
            storage_path=test_storage_path
        )
        
        # Test core initialization logic
        assert processor.repo_url == "https://github.com/test/repo.git"
        assert processor.branch == "main"
        assert processor.storage_path == test_storage_path
        assert processor.username == "testuser"
        assert processor.access_token == "testtoken"
    
    def test_init_validation(self, test_storage_path):
        """Test initialization parameter validation."""
        # Test missing repo URL
        with pytest.raises(GitProcessingError, match="Repository URL is required"):
            GitProcessor(
                repo_url="",
                branch="main",
                username="testuser",
                access_token="testtoken",
                storage_path=test_storage_path
            )
        
        # Test missing branch
        with pytest.raises(GitProcessingError, match="Branch name is required"):
            GitProcessor(
                repo_url="https://github.com/test/repo.git",
                branch="",
                username="testuser",
                access_token="testtoken",
                storage_path=test_storage_path
            )
        
        # Test missing username
        with pytest.raises(GitProcessingError, match="Username is required"):
            GitProcessor(
                repo_url="https://github.com/test/repo.git",
                branch="main",
                username="",
                access_token="testtoken",
                storage_path=test_storage_path
            )
        
        # Test missing access token
        with pytest.raises(GitProcessingError, match="Access token is required"):
            GitProcessor(
                repo_url="https://github.com/test/repo.git",
                branch="main",
                username="testuser",
                access_token="",
                storage_path=test_storage_path
            )
        
        # Test missing storage path
        with pytest.raises(GitProcessingError, match="Storage path is required"):
            GitProcessor(
                repo_url="https://github.com/test/repo.git",
                branch="main",
                username="testuser",
                access_token="testtoken",
                storage_path=None
            )
    
    def test_commit_message_path_validation(self, test_storage_path):
        """Test message path validation in commit_message."""
        processor = GitProcessor(
            repo_url="https://github.com/test/repo.git",
            branch="main",
            username="testuser", 
            access_token="testtoken",
            storage_path=test_storage_path
        )
        
        # Test with valid path
        message_path = test_storage_path / "messages" / "2024-01-11" / "message_123.json"
        processor.commit_message(message_path)  # Should not raise
        
        # Test with path outside storage
        invalid_path = Path("/tmp/outside/message.json") 
        with pytest.raises(GitProcessingError, match="outside storage directory"):
            processor.commit_message(invalid_path)
            
        # Test with non-existent path
        missing_path = test_storage_path / "messages" / "missing.json"
        with pytest.raises(GitProcessingError, match="does not exist"):
            processor.commit_message(missing_path)
    
    def test_commit_media_path_validation(self, test_storage_path):
        """Test media path validation in commit_media."""
        processor = GitProcessor(
            repo_url="https://github.com/test/repo.git",
            branch="main",
            username="testuser",
            access_token="testtoken", 
            storage_path=test_storage_path
        )
        
        # Test with valid paths
        media_paths = [
            test_storage_path / "media" / "2024-01-11" / "photo_123.jpg",
            test_storage_path / "media" / "2024-01-11" / "document_456.pdf"
        ]
        processor.commit_media(media_paths)  # Should not raise
        
        # Test with mixed valid/invalid paths
        mixed_paths = [
            test_storage_path / "media" / "2024-01-11" / "photo_123.jpg",
            Path("/tmp/outside/doc.pdf")
        ]
        with pytest.raises(GitProcessingError, match="outside storage directory"):
            processor.commit_media(mixed_paths)
        
        # Test with empty list
        with pytest.raises(GitProcessingError, match="No media paths provided"):
            processor.commit_media([])
    
    def test_push_changes_validation(self, test_storage_path):
        """Test push changes validation."""
        # Create a mock repository
        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_repo.remotes.origin = mock_remote
        
        processor = GitProcessor(
            repo_url="https://github.com/test/repo.git",
            branch="main",
            username="testuser",
            access_token="testtoken",
            storage_path=test_storage_path
        )
        processor._repo = mock_repo  # Replace the real repo with our mock

        # Test basic push validation
        processor.push_changes()  # Should not raise
        mock_remote.push.assert_called_once_with("main")

        # Test empty repo_url validation
        processor.repo_url = ""
        with pytest.raises(GitProcessingError, match="Repository URL not configured"):
            processor.push_changes()

        # Test push failure
        processor.repo_url = "https://github.com/test/repo.git"  # Restore URL
        mock_remote.push.side_effect = git.GitCommandError("push", "Network error")
        with pytest.raises(GitProcessingError, match="Failed to push changes to remote"):
            processor.push_changes() 