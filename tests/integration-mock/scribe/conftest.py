import pytest
from unittest.mock import Mock, AsyncMock
from chronicler.scribe.interface import ScribeConfig
from chronicler.storage.config_interface import ConfigStorageAdapter

@pytest.fixture
def test_config():
    """Provides a test scribe configuration"""
    return ScribeConfig(
        token="test_token",
        admin_users=[123],
        github_token=None,
        github_repo=None
    )

@pytest.fixture
def mock_config_store():
    """Mock the config storage adapter"""
    store = Mock(spec=ConfigStorageAdapter)
    store.load = AsyncMock(return_value={})
    store.save = AsyncMock()
    return store 