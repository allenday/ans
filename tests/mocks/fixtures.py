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