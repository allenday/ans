"""Mock storage implementations for testing."""
from pathlib import Path

class MockStorageCoordinator:
    """Mock storage coordinator for testing."""
    
    def __init__(self, base_path: Path):
        """Initialize mock storage."""
        self.base_path = base_path
        self.saved_messages = []
        self.saved_attachments = []
        self.topics = {}
        self.github_token = None
        self.github_repo = None
        
    def init_storage(self, user_id: int) -> None:
        """Initialize storage for a user."""
        pass
        
    def create_topic(self, user_id: int, topic_name: str) -> None:
        """Create a new topic."""
        self.topics[(user_id, topic_name)] = {
            'messages': [],
            'attachments': []
        }
        
    def save_message(self, user_id: int, topic_name: str, message: dict) -> None:
        """Save a message to a topic."""
        if (user_id, topic_name) not in self.topics:
            self.create_topic(user_id, topic_name)
        self.saved_messages.append((user_id, topic_name, message))
        self.topics[(user_id, topic_name)]['messages'].append(message)
        
    def save_attachment(self, user_id: int, topic_name: str, file_path: str | Path, attachment_name: str) -> None:
        """Save an attachment."""
        if (user_id, topic_name) not in self.topics:
            self.create_topic(user_id, topic_name)
        self.saved_attachments.append((user_id, topic_name, file_path, attachment_name))
        self.topics[(user_id, topic_name)]['attachments'].append({
            'path': str(file_path),
            'name': attachment_name
        })
        
    def sync(self, user_id: int) -> None:
        """Synchronize with remote storage."""
        pass
        
    def set_github_config(self, token: str, repo: str) -> None:
        """Set GitHub configuration."""
        self.github_token = token
        self.github_repo = repo
        
    def topic_exists(self, user_id: int, topic_name: str) -> bool:
        """Check if a topic exists."""
        return (user_id, topic_name) in self.topics