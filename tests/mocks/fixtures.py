"""Centralized pytest fixtures for testing."""
import os
import shutil
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from pathlib import Path
import asyncio
from chronicler.transports.telegram_bot_transport import TelegramBotTransport

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
from chronicler.exceptions import TransportError, TransportAuthenticationError

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

@pytest_asyncio.fixture
async def mock_http_request():
    """Mock HTTP request for testing."""
    # Create mock request
    mock_request = AsyncMock()
    mock_request.initialize = AsyncMock()
    mock_request.shutdown = AsyncMock()

    # Mock do_request to validate tokens
    async def mock_do_request(url, method):
        if "getMe" in url:
            token = url.split("/bot")[1].split("/")[0]
            if token == "test_token":
                return 200, {"ok": True, "result": {"id": 123, "first_name": "Test Bot", "username": "test_bot"}}
            return 401, {"ok": False, "error_code": 401, "description": "Unauthorized"}
        return 200, {"ok": True}

    mock_request.do_request = AsyncMock(side_effect=mock_do_request)
    return mock_request

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

@pytest_asyncio.fixture
async def mock_bot_runner(mock_telegram_bot, coordinator_mock):
    """Create a mock bot runner setup with all required components."""
    # Create mock transport
    mock_transport = TelegramBotTransport("test_token")
    mock_transport._app = mock_telegram_bot
    mock_transport._bot = mock_telegram_bot.bot
    mock_transport._initialized = True  # Set _initialized instead of is_running
    mock_transport.authenticate = AsyncMock()  # Add authenticate method
    mock_transport.start = AsyncMock()  # Add start method
    mock_transport.stop = AsyncMock()  # Add stop method

    # Mock storage using coordinator_mock
    mock_storage = AsyncMock()
    mock_storage.start = AsyncMock()
    mock_storage.stop = AsyncMock()
    mock_storage.coordinator = coordinator_mock
    mock_storage.is_initialized = AsyncMock(return_value=False)  # Add is_initialized method
    mock_storage.init_storage = AsyncMock()  # Add init_storage method
    mock_storage.create_topic = AsyncMock()  # Add create_topic method
    mock_storage.save_message = AsyncMock()  # Add save_message method

    # Mock command processor
    mock_cmd_proc = AsyncMock()
    mock_cmd_proc.register_handler = MagicMock()  # Not async
    mock_cmd_proc.start = AsyncMock()
    mock_cmd_proc.stop = AsyncMock()
    mock_cmd_proc.process = AsyncMock()  # Add process method

    # Mock pipeline
    mock_pipeline = AsyncMock()
    mock_pipeline.add_processor = MagicMock()  # Not async
    mock_pipeline.start = AsyncMock()
    mock_pipeline.stop = AsyncMock()
    mock_pipeline.process = AsyncMock()  # Add process method

    # Create a stop event that's already set
    stop_event = asyncio.Event()
    stop_event.set()

    # Mock event loop
    mock_loop = MagicMock()
    def add_signal_handler(sig, callback):
        callback()  # Call the handler immediately
    mock_loop.add_signal_handler = MagicMock(side_effect=add_signal_handler)

    # Set up error handling for invalid token
    async def mock_authenticate():
        if mock_transport.token == "invalid_token":
            mock_transport._initialized = False
            raise TransportAuthenticationError("Token validation failed")
        mock_transport._initialized = True
        return None
    mock_transport.authenticate.side_effect = mock_authenticate

    # Return all mocks in a dict for easy access
    return {
        'transport': mock_transport,
        'storage': mock_storage,
        'cmd_proc': mock_cmd_proc,
        'pipeline': mock_pipeline,
        'stop_event': stop_event,
        'loop': mock_loop
    } 