"""Storage-related pytest fixtures."""
import pytest
from unittest.mock import AsyncMock, create_autospec

from chronicler.storage import StorageAdapter
from chronicler.storage.coordinator import StorageCoordinator

@pytest.fixture
def storage_mock():
    """Create a mock storage adapter."""
    storage = create_autospec(StorageAdapter)
    storage.init_storage.return_value = storage
    storage.create_topic.return_value = None
    storage.save_message = AsyncMock(return_value="msg_123")
    storage.save_attachment = AsyncMock(return_value=None)
    storage.sync = AsyncMock(return_value=None)
    storage.set_github_config = AsyncMock(return_value=None)
    storage.is_initialized.return_value = True
    return storage

@pytest.fixture
def coordinator_mock():
    """Create a mock storage coordinator."""
    coordinator = create_autospec(StorageCoordinator)
    coordinator.init_storage = AsyncMock()
    coordinator.create_topic = AsyncMock()
    coordinator.save_message = AsyncMock()
    coordinator.save_attachment = AsyncMock()
    coordinator.sync = AsyncMock()
    coordinator.set_github_config = AsyncMock()
    coordinator.is_initialized = AsyncMock(return_value=True)
    return coordinator 