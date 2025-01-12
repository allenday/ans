"""Mock storage implementations for testing."""
from pathlib import Path
from chronicler.storage.interface import StorageAdapter, User, Topic, Message, Attachment

class MockStorageCoordinator(StorageAdapter):
    """Mock storage coordinator for testing."""
    
    def __init__(self, storage_path: Path):
        """Initialize mock storage."""
        self.storage_path = storage_path
        self.saved_messages = []
        self.saved_attachments = []
        self.topics = {}
        self._initialized = False
        self.github_token = None
        self.github_repo = None
        
    async def init_storage(self, user: User) -> 'StorageAdapter':
        """Initialize storage for a user."""
        self._initialized = True
        return self
        
    async def create_topic(self, topic: Topic | str, ignore_exists: bool = False, **kwargs) -> None:
        """Create a new topic."""
        if isinstance(topic, str):
            topic = Topic(id=topic, name=topic, metadata=kwargs)
        self.topics[topic.id] = topic
        
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message to a topic."""
        self.saved_messages.append((topic_id, message))
        
    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        """Save an attachment."""
        self.saved_attachments.append((topic_id, message_id, attachment))
        
    async def sync(self) -> None:
        """Synchronize with remote storage."""
        pass
        
    async def set_github_config(self, token: str, repo: str) -> None:
        """Set GitHub configuration."""
        self.github_token = token
        self.github_repo = repo
        
    def is_initialized(self) -> bool:
        """Check if storage is initialized."""
        return self._initialized