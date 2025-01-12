"""Mock implementations for storage adapters."""
from pathlib import Path
from chronicler.storage.interface import User, StorageAdapter
from chronicler.storage.filesystem import FileSystemStorage
from chronicler.storage.serializer import MessageSerializer
from chronicler.storage.coordinator import StorageCoordinator

class MockGitAdapter(StorageAdapter):
    """Mock implementation of Git storage adapter."""
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path

    async def init_storage(self, user: User) -> None:
        """Mock initialization."""
        pass

    async def create_topic(self, user: User, topic: str) -> None:
        """Mock topic creation."""
        pass

    async def save_message(self, user: User, topic: str, message: dict) -> None:
        """Mock message saving."""
        pass

    async def save_attachment(self, user: User, topic: str, attachment_info: dict, file_data: bytes) -> None:
        """Mock attachment saving."""
        pass

    async def set_github_config(self, user: User, repo_url: str, token: str) -> None:
        """Mock GitHub config setting."""
        pass

    async def sync(self, user: User) -> None:
        """Mock sync operation."""
        pass

class MockStorageCoordinator(StorageCoordinator):
    """Mock implementation of storage coordinator."""
    def __init__(self, storage_path: Path):
        super().__init__(storage_path)
        self._initialized = True
        self.git_storage = MockGitAdapter(storage_path)
        self.file_storage = FileSystemStorage(storage_path)
        self.serializer = MessageSerializer()

    async def is_initialized(self, user: User) -> bool:
        """Mock initialization check."""
        return self._initialized

    async def init_storage(self, user: User) -> None:
        """Mock initialization of storage for a user."""
        pass

    async def create_topic(self, user: User, topic: str) -> None:
        """Mock topic creation."""
        pass

    async def save_message(self, user: User, topic: str, message: dict) -> None:
        """Mock message saving."""
        pass 