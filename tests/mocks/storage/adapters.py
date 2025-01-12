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