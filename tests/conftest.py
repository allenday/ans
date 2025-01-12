"""Test configuration and shared fixtures."""
import os
import sys
import pytest
import logging
import pytest_asyncio
from chronicler.storage.interface import User
from chronicler.transports.telegram_factory import TelegramTransportFactory
from chronicler.logging import get_logger, configure_logging
import asyncio
from pathlib import Path

# Import centralized fixtures
from tests.mocks.fixtures import mock_session_path, mock_telethon, mock_telegram_bot

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Add test directories to Python path
test_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), '00-unit')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '01-mock')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '02-live'))
]
for path in test_paths:
    if path not in sys.path:
        sys.path.insert(0, path)

logger = get_logger(__name__)

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "scribe: mark test as scribe test")
    config.addinivalue_line("markers", "storage: mark test as storage test")

# General test fixtures

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Set up logging for all tests."""
    caplog.set_level(logging.DEBUG)
    yield

@pytest.fixture
def test_log_level():
    """Set test log level"""
    return logging.DEBUG

@pytest.fixture
def test_config():
    """Create test config"""
    from chronicler.scribe.interface import ScribeConfig
    return ScribeConfig(telegram_token=os.environ["TELEGRAM_BOT_TOKEN"])

@pytest.fixture
def test_user():
    """Create a test user"""
    return User(id="test_user", name="Test User")

@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Configure logging for all tests."""
    configure_logging(level='DEBUG')
    # Set root logger level to ensure all logs are captured
    logging.getLogger().setLevel(logging.DEBUG)
    yield

# Live test fixtures

@pytest_asyncio.fixture
async def user_transport():
    """Create a real user transport."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        api_id=os.environ["TELEGRAM_API_ID"],
        api_hash=os.environ["TELEGRAM_API_HASH"],
        phone_number=os.environ["TELEGRAM_PHONE_NUMBER"]
    )
    await transport.start()
    yield transport
    await transport.stop()

@pytest_asyncio.fixture
async def bot_transport():
    """Create a real bot transport."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"]
    )
    await transport.start()
    yield transport
    await transport.stop()

@pytest_asyncio.fixture
async def test_bot_transport():
    """Create a real test bot transport."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        bot_token=os.environ["TELEGRAM_TEST_BOT_TOKEN"]
    )
    await transport.start()
    yield transport
    await transport.stop()

@pytest_asyncio.fixture(autouse=True)
async def test_cleanup():
    """Cleanup after each test."""
    yield
    
    # Cancel any remaining tasks
    for task in asyncio.all_tasks():
        if not task.done() and task != asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass 