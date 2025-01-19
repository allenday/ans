"""Mock implementations for storage adapters."""
from pathlib import Path
from chronicler.storage.git import GitStorageAdapter

class MockGitAdapter(GitStorageAdapter):
    """Mock implementation of Git storage adapter."""
    def __init__(self, base_path: str | Path):
        """Initialize mock git storage."""
        super().__init__(base_path)
        
    def init_storage(self, user_id: int) -> None:
        """Mock initialization."""
        pass
        
    def create_topic(self, user_id: int, topic_name: str) -> None:
        """Mock topic creation."""
        pass
        
    def save_message(self, user_id: int, topic_name: str, message: dict) -> None:
        """Mock message saving."""
        pass
        
    def save_attachment(self, user_id: int, topic_name: str, file_path: str | Path, attachment_name: str) -> None:
        """Mock attachment saving."""
        pass
        
    def set_github_config(self, token: str, repo: str) -> None:
        """Mock GitHub config setting."""
        pass
        
    def sync(self, user_id: int) -> None:
        """Mock sync operation."""
        pass
        
    def topic_exists(self, user_id: int, topic_name: str) -> bool:
        """Mock topic existence check."""
        return True 