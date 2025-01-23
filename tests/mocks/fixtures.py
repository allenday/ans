"""Centralized pytest fixtures for testing."""
import os
import shutil
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from pathlib import Path

# Patch httpx.AsyncClient before any imports
class MockAsyncClient:
    def __init__(self, **kwargs):
        self.is_closed = False
        self.timeout = Mock(read=None, write=None, connect=None, pool=None)

    async def request(self, method, url, **kwargs):
        if "invalid_token" in url:
            return MockResponse(404, b'{"ok":false,"error_code":404,"description":"Not Found"}')
        elif "valid_token" in url:
            return MockResponse(200, b'{"ok":true,"result":{"id":123,"first_name":"Test Bot","username":"test_bot","can_join_groups":true,"can_read_all_group_messages":false,"supports_inline_queries":false,"is_bot":true}}')
        else:
            return MockResponse(404, b'{"ok":false,"error_code":404,"description":"Not Found"}')

    async def post(self, url, **kwargs):
        return await self.request("POST", url, **kwargs)

    async def aclose(self):
        self.is_closed = True

class MockResponse:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content

# Patch httpx.AsyncClient before importing telegram
import httpx
httpx.AsyncClient = MockAsyncClient

from telegram.error import InvalidToken
from chronicler.exceptions import TransportError
from tests.mocks.transports import create_mock_telethon

class MockHTTPXRequest:
    async def do_request(self, url, method, **kwargs):
        if "invalid_token" in url:
            return 404, b'{"ok":false,"error_code":404,"description":"Not Found"}'
        elif "valid_token" in url:
            return 200, b'{"ok":true,"result":{"id":123,"first_name":"Test Bot","username":"test_bot","can_join_groups":true,"can_read_all_group_messages":false,"supports_inline_queries":false,"is_bot":true}}'
        else:
            raise InvalidToken("Token validation failed")

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    async def post(self, url, **kwargs):
        code, payload = await self.do_request(url=url, method="POST")
        return payload

@pytest.fixture
def mock_http_request():
    """Mock HTTP request for testing."""
    return MockHTTPXRequest()

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
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock:
        client = create_mock_telethon()
        
        # Mock session with custom path
        client.session = MagicMock()
        client.session.save = MagicMock()
        client.session.session_file = os.path.join(mock_session_path, "test_session.session")
        
        mock.return_value = client
        yield mock

@pytest_asyncio.fixture
async def mock_token_bot(monkeypatch, mock_http_request):
    """Mock telegram bot for testing token validation."""
    # Create mock bot
    mock_bot = AsyncMock()
    mock_bot.token = None
    mock_bot._initialized = False
    mock_bot.send_message = AsyncMock()
    mock_bot.send_photo = AsyncMock()

    # Create mock app with all required methods as AsyncMock instances
    mock_app = AsyncMock(spec=False)
    mock_app.bot = mock_bot
    mock_app.handlers = {0: []}  # Group 0 is default for command handlers
    mock_app.stop = AsyncMock()
    mock_app.shutdown = AsyncMock()
    mock_app.initialize = AsyncMock()
    mock_app.update_queue = AsyncMock()
    mock_app.updater = AsyncMock()
    mock_app.job_queue = AsyncMock()
    mock_app.create_task = AsyncMock()
    
    # Create start and add_handler mocks separately to ensure they're not bound
    start_mock = AsyncMock(name="app.start")
    add_handler_mock = AsyncMock(name="app.add_handler")
    mock_app.__dict__["start"] = start_mock  # Bypass descriptor binding
    mock_app.__dict__["add_handler"] = add_handler_mock  # Bypass descriptor binding

    # Set up bidirectional references
    mock_bot._app = mock_app
    mock_app.bot = mock_bot

    # Create mock builder that validates tokens
    class MockBuilder:
        def __init__(self):
            self._token = None
            self._bot = mock_bot
            self._app = mock_app

        def token(self, token):
            if not token:
                raise InvalidToken("Invalid token: You must pass the token you received from https://t.me/Botfather!")
            self._token = token
            self._bot.token = token
            return self

        def build(self):
            if not self._token:
                raise InvalidToken("Invalid token: You must pass the token you received from https://t.me/Botfather!")
            return self._app

    # Mock initialize to set up the bot properly
    async def mock_initialize():
        if not mock_bot.token:
            raise InvalidToken("Token not set")
        await mock_bot.get_me()
        mock_bot._initialized = True

    mock_app.initialize = AsyncMock(side_effect=mock_initialize)

    # Mock get_me to validate token
    async def mock_get_me():
        if not mock_bot.token:
            raise InvalidToken("Token not set")
        code, payload = await mock_http_request.do_request(
            url=f"https://api.telegram.org/bot{mock_bot.token}/getMe",
            method="POST"
        )
        if code == 200:
            return {"id": 123, "first_name": "Test Bot", "username": "test_bot"}
        raise InvalidToken("Token validation failed")

    mock_bot.get_me = AsyncMock(side_effect=mock_get_me)

    # Mock HTTPXRequest to use our mock request
    class MockHTTPXRequest:
        def __init__(self):
            self._request = mock_http_request

        async def do_request(self, url, method, request_data=None, **kwargs):
            return await self._request.do_request(url=url, method=method)

        async def post(self, url, **kwargs):
            code, payload = await self.do_request(url=url, method="POST")
            return payload

        async def initialize(self):
            await self._request.initialize()

        async def shutdown(self):
            await self._request.shutdown()

    def mock_builder_init():
        return MockBuilder()

    # Patch both ApplicationBuilder and HTTPXRequest before importing
    monkeypatch.setattr("telegram.request.HTTPXRequest", MockHTTPXRequest)
    monkeypatch.setattr("telegram.ext.ApplicationBuilder", mock_builder_init)

    # Create mock request objects
    mock_bot._request = [MockHTTPXRequest(), MockHTTPXRequest()]  # Primary and media requests

    return mock_bot

@pytest.fixture
def mock_app_bot(monkeypatch):
    """Create a mock Telegram bot with all required methods as AsyncMock instances."""
    # Create mock bot
    mock_bot = AsyncMock()
    mock_bot.token = None
    mock_bot._initialized = False
    mock_bot.send_message = AsyncMock()
    mock_bot.send_photo = AsyncMock()
    mock_bot.get_me = AsyncMock()

    # Create mock app with all required methods
    mock_app = AsyncMock()
    
    # Create separate AsyncMock instances for methods to avoid descriptor binding
    start_mock = AsyncMock(name="app.start")
    add_handler_mock = AsyncMock(name="app.add_handler")
    initialize_mock = AsyncMock(name="app.initialize")
    stop_mock = AsyncMock(name="app.stop")
    shutdown_mock = AsyncMock(name="app.shutdown")
    
    # Bypass descriptor binding by setting in __dict__
    mock_app.__dict__.update({
        "start": start_mock,
        "add_handler": add_handler_mock,
        "initialize": initialize_mock,
        "stop": stop_mock,
        "shutdown": shutdown_mock,
        "bot": mock_bot
    })
    mock_bot._app = mock_app

    # Create mock request for token validation
    mock_request = MockHTTPXRequest()
    mock_bot._request = mock_request
    
    class MockBuilder:
        def __init__(self):
            self._token = None
            self._bot = mock_bot
            self._app = mock_app
            
        def token(self, token):
            self._token = token
            self._bot.token = token  # Set token on bot as well
            return self
            
        def build(self):
            if not self._token:
                raise RuntimeError("No bot token was set")
            if "invalid_token" in self._token:
                raise InvalidToken("Invalid token")
            return self._app

    def mock_builder():
        return MockBuilder()

    # Patch both ApplicationBuilder and HTTPXRequest
    monkeypatch.setattr("telegram.ext.ApplicationBuilder", mock_builder)
    monkeypatch.setattr("telegram.request.HTTPXRequest", MockHTTPXRequest)

    return mock_bot

@pytest.fixture
def assert_transport_error_async():
    """Fixture to assert that an async function raises TransportError with expected message."""
    async def _assert_transport_error_async(func, expected_message, post_error_assertions=None):
        with pytest.raises((TransportError, InvalidToken), match=expected_message):
            await func()
        if post_error_assertions:
            post_error_assertions()
    return _assert_transport_error_async 