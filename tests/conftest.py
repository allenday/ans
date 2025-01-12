"""Test configuration and shared fixtures."""
import os
import sys
import pytest
import logging
import tempfile
import shutil
import asyncio
import uuid
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from chronicler.storage.interface import User
from chronicler.transports.telegram import TelegramTransportFactory

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

logger = logging.getLogger(__name__)

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
def setup_test_env():
    """Set up test environment."""
    # Add any test environment setup here
    pass

# Mock fixtures

@pytest.fixture
def mock_session_path(tmp_path):
    """Create a temporary directory for Telethon session files."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    
    # Ensure the directory exists and is empty
    if session_dir.exists():
        for file in session_dir.glob("*.session"):
            try:
                file.unlink()
            except Exception:
                pass
            
    yield str(session_dir)
    
    # Cleanup: Close any open connections and remove files
    try:
        for file in session_dir.glob("*.session"):
            try:
                file.unlink()
            except Exception:
                pass
        shutil.rmtree(str(session_dir))
    except Exception:
        pass

@pytest.fixture
def mock_telethon(mock_session_path):
    """Create a mock Telethon client."""
    mock = AsyncMock()
    
    # Mock connect and disconnect
    mock.connect = AsyncMock(return_value=True)
    mock.disconnect = AsyncMock(return_value=True)
    mock.is_user_authorized = AsyncMock(return_value=True)
    
    # Mock message sending
    mock.send_message = AsyncMock()
    mock.send_file = AsyncMock()
    
    # Mock event handling
    mock.on = MagicMock()
    mock.add_event_handler = AsyncMock()
    mock.remove_event_handler = AsyncMock()
    
    # Mock session with custom path
    mock.session = MagicMock()
    mock.session.save = MagicMock()
    mock.session.session_file = os.path.join(mock_session_path, "test_session.session")
    
    return mock

@pytest.fixture
def mock_python_telegram_bot():
    """Create a mock python-telegram-bot Application."""
    mock = AsyncMock()
    
    # Mock bot instance with user info
    mock.bot = AsyncMock()
    mock.bot.get_me = AsyncMock(return_value=MagicMock(
        id=12345,
        username="test_bot",
        first_name="Test Bot",
        is_bot=True
    ))
    mock.bot.send_message = AsyncMock(return_value=MagicMock(message_id=1))
    mock.bot.send_photo = AsyncMock(return_value=MagicMock(message_id=2))
    mock.bot.send_document = AsyncMock(return_value=MagicMock(message_id=3))
    
    # Mock application methods
    mock.initialize = AsyncMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.running = True
    
    # Mock updater
    mock.updater = AsyncMock()
    mock.updater.start_polling = AsyncMock()
    mock.updater.stop = AsyncMock()
    
    # Mock handler management
    mock.add_handler = MagicMock()
    mock.remove_handler = MagicMock()
    
    # Mock builder for token validation
    class MockBuilder:
        def token(self, token):
            if not token:
                raise ValueError("Token cannot be empty")
            if token == os.environ["TELEGRAM_BOT_TOKEN"]:
                return self
            raise ValueError(f"Invalid token: {token}")
        def build(self):
            return mock
    mock.builder = MagicMock(return_value=MockBuilder())
    
    return mock 

# Live test fixtures

@pytest_asyncio.fixture
async def user_transport(mock_session_path):
    """Create a real user transport."""
    # Check required environment variables
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    phone_number = os.environ.get("TELEGRAM_PHONE_NUMBER")
    
    if not all([api_id, api_hash, phone_number]):
        pytest.skip("Missing required environment variables for user transport")
    
    # Create unique session name for this test
    session_name = f"test_session_{uuid.uuid4().hex}"
    session_path = os.path.join(mock_session_path, session_name)
    
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        api_id=api_id,
        api_hash=api_hash,
        phone_number=phone_number,
        session_name=session_name
    )
    await transport.start()
    yield transport
    await transport.stop()
    
    # Cleanup session file
    try:
        os.remove(f"{session_path}.session")
    except Exception:
        pass

@pytest_asyncio.fixture
async def bot_transport(mock_session_path):
    """Create a real bot transport."""
    # Check required environment variables
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        pytest.skip("TELEGRAM_BOT_TOKEN not set")
    
    # Create unique session name for this test
    session_name = f"test_bot_{uuid.uuid4().hex}"
    session_path = os.path.join(mock_session_path, session_name)
    
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        bot_token=bot_token,
        session_name=session_name
    )
    await transport.start()
    yield transport
    await transport.stop()
    
    # Cleanup session file
    try:
        os.remove(f"{session_path}.session")
    except Exception:
        pass

@pytest_asyncio.fixture
async def test_bot_transport(mock_session_path):
    """Create a real test bot transport."""
    # Check required environment variables
    test_bot_token = os.environ.get("TELEGRAM_TEST_BOT_TOKEN")
    if not test_bot_token:
        pytest.skip("TELEGRAM_TEST_BOT_TOKEN not set")
    
    # Create unique session name for this test
    session_name = f"test_bot2_{uuid.uuid4().hex}"
    session_path = os.path.join(mock_session_path, session_name)
    
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        bot_token=test_bot_token,
        session_name=session_name
    )
    await transport.start()
    yield transport
    await transport.stop()
    
    # Cleanup session file
    try:
        os.remove(f"{session_path}.session")
    except Exception:
        pass

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
            except (asyncio.CancelledError, Exception):
                pass 