import pytest
import logging
from chronicler.storage.interface import User

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "scribe: mark test as scribe test")
    config.addinivalue_line("markers", "storage: mark test as storage test")

@pytest.fixture
def test_log_level():
    """Set test log level"""
    return logging.DEBUG

@pytest.fixture
def test_config():
    """Create test config"""
    from chronicler.scribe.interface import ScribeConfig
    return ScribeConfig(telegram_token="test_token")

@pytest.fixture
def test_user():
    """Create a test user"""
    return User(id="test_user", name="Test User") 