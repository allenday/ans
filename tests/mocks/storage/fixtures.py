"""Storage-related pytest fixtures."""
import pytest
from unittest.mock import AsyncMock, create_autospec

from chronicler.storage import StorageAdapter

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