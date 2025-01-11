import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch
from chronicler.processors.git_processor import GitProcessor, GitProcessingError

@pytest.fixture
def git_processor():
    """Create a GitProcessor instance for testing."""
    return GitProcessor(
        repo_url="https://github.com/test/repo.git",
        branch="main",
        username="testuser",
        access_token="testtoken",
        storage_path=Path("/tmp/test-storage")
    )

@pytest.fixture
def mock_repo():
    """Create a mock git.Repo object."""
    mock = Mock()
    mock.index = Mock()
    mock.remotes = Mock()
    mock.remotes.origin = Mock()
    return mock

class TestGitProcessor:
    """Test suite for GitProcessor."""
    
    def test_init_processor(self, git_processor):
        """Test GitProcessor initialization."""
        assert git_processor.repo_url == "https://github.com/test/repo.git"
        assert git_processor.branch == "main"
        assert isinstance(git_processor.storage_path, Path)
    
    @patch('git.Repo')
    def test_commit_message(self, mock_repo_class, git_processor):
        """Test committing a new message."""
        mock_repo = mock_repo_class.return_value
        message_path = Path("/tmp/test-storage/messages/2024-01-11/message_123.json")
        
        git_processor.commit_message(message_path)
        
        # Verify git operations
        mock_repo.index.add.assert_called_once_with([str(message_path)])
        mock_repo.index.commit.assert_called_once()
        commit_msg = mock_repo.index.commit.call_args[0][0]
        assert "Add message" in commit_msg
        assert "message_123.json" in commit_msg
    
    @patch('git.Repo')
    def test_commit_media(self, mock_repo_class, git_processor):
        """Test committing media files."""
        mock_repo = mock_repo_class.return_value
        media_paths = [
            Path("/tmp/test-storage/media/2024-01-11/photo_123.jpg"),
            Path("/tmp/test-storage/media/2024-01-11/document_456.pdf")
        ]
        
        git_processor.commit_media(media_paths)
        
        # Verify git operations
        mock_repo.index.add.assert_called_once_with([str(p) for p in media_paths])
        mock_repo.index.commit.assert_called_once()
        commit_msg = mock_repo.index.commit.call_args[0][0]
        assert "Add media files" in commit_msg
        assert "photo_123.jpg" in commit_msg
        assert "document_456.pdf" in commit_msg
    
    @patch('git.Repo')
    def test_push_changes_success(self, mock_repo_class, git_processor):
        """Test successful push to remote."""
        mock_repo = mock_repo_class.return_value
        
        git_processor.push_changes()
        
        mock_repo.remotes.origin.push.assert_called_once_with("main")
    
    @patch('git.Repo')
    def test_push_changes_failure(self, mock_repo_class, git_processor):
        """Test handling push failure."""
        mock_repo = mock_repo_class.return_value
        mock_repo.remotes.origin.push.side_effect = Exception("Network error")
        
        with pytest.raises(GitProcessingError) as exc_info:
            git_processor.push_changes()
        
        assert "Failed to push changes" in str(exc_info.value)
        mock_repo.remotes.origin.push.assert_called_once_with("main") 