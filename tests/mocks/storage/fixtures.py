"""Storage-related pytest fixtures."""
import pytest
from unittest.mock import MagicMock, create_autospec

from chronicler.storage import StorageAdapter
from chronicler.storage.coordinator import StorageCoordinator

@pytest.fixture
def storage_mock():
    """Create a mock storage adapter."""
    storage = create_autospec(StorageAdapter)
    storage.init_storage.return_value = storage
    storage.create_topic.return_value = None
    storage.save_message = MagicMock(return_value="msg_123")
    storage.save_attachment = MagicMock(return_value=None)
    storage.sync = MagicMock(return_value=None)
    storage.set_github_config = MagicMock(return_value=None)
    storage.is_initialized.return_value = True
    return storage

@pytest.fixture
def coordinator_mock():
    """Create a mock storage coordinator."""
    coordinator = create_autospec(StorageCoordinator)
    coordinator.init_storage = create_autospec(StorageCoordinator.init_storage)
    coordinator.create_topic = create_autospec(StorageCoordinator.create_topic)
    coordinator.save_message = create_autospec(StorageCoordinator.save_message)
    coordinator.save_attachment = create_autospec(StorageCoordinator.save_attachment)
    coordinator.sync = create_autospec(StorageCoordinator.sync)
    coordinator.set_github_config = create_autospec(StorageCoordinator.set_github_config)
    coordinator.topic_exists = create_autospec(StorageCoordinator.topic_exists, return_value=True)
    return coordinator 