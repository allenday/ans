"""Storage-related pytest fixtures."""
import pytest
from unittest.mock import MagicMock, create_autospec, AsyncMock

from chronicler.storage.coordinator import StorageCoordinator

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
    coordinator.is_initialized = AsyncMock(return_value=False)  # Mock is_initialized as an async function
    return coordinator 