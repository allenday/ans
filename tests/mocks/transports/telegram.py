"""Mock implementations for Telegram transports."""
import pytest
from unittest.mock import AsyncMock, Mock, call, MagicMock, patch
from telegram.ext import ApplicationBuilder, CommandHandler, ExtBot, Application
from telegram.error import InvalidToken
from typing import Optional, Tuple, Dict
from telegram.request import RequestData, BaseRequest
import json
from telegram import Bot
import asyncio

from chronicler.exceptions import TransportError
from chronicler.frames import CommandFrame
from chronicler.transports.events import EventMetadata
from chronicler.transports.telegram_bot_transport import TelegramBotTransport, TelegramBotEvent

from telethon import events

class MockHTTPXRequest(BaseRequest):
    """Mock request handler for testing."""

    async def initialize(self) -> None:
        """Mock initialization."""
        pass

    async def shutdown(self) -> None:
        """Mock shutdown."""
        pass

    async def _request_wrapper(
        self,
        url: str,
        method: str,
        request_data: Optional[RequestData] = None,
        read_timeout: Optional[float] = None,
        write_timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
        pool_timeout: Optional[float] = None,
    ) -> bytes:
        """Mock request wrapper that always returns success."""
        return json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()

    async def do_request(
        self,
        url: str,
        method: str,
        request_data: Optional[RequestData] = None,
        read_timeout: Optional[float] = None,
        write_timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
        pool_timeout: Optional[float] = None,
    ) -> Tuple[int, bytes]:
        """Mock request that returns success."""
        return 200, json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()

    def parse_json_payload(self, payload: bytes) -> Dict:
        """Parse JSON payload."""
        return json.loads(payload.decode())

    async def post(
        self,
        url: str,
        request_data: Optional[RequestData] = None,
        read_timeout: Optional[float] = None,
        write_timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
        pool_timeout: Optional[float] = None,
    ) -> bytes:
        """Mock post request that returns success."""
        return json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()

class MockBot:
    """Mock Bot class that uses our mock request objects."""
    def __init__(self, token: str, **kwargs):
        self.token = token
        self._request = [MockHTTPXRequest(), MockHTTPXRequest()]  # Use the same request object for both slots
        self._initialized = False
        self._app = None
        self._me = {
            "id": 123456789,
            "is_bot": True,
            "first_name": "Test Bot",
            "username": "test_bot",
            "can_join_groups": True,
            "can_read_all_group_messages": True,
            "supports_inline_queries": False
        }
        self._LOGGER = MagicMock()  # Add logger mock
        self.send_message = AsyncMock()
        self.send_photo = AsyncMock()

    async def initialize(self) -> None:
        """Mock initialization that always succeeds."""
        if self._initialized:
            self._LOGGER.debug("This Bot is already initialized.")
            return
        await asyncio.gather(self._request[0].initialize(), self._request[1].initialize())
        await self.get_me()  # Ensure get_me succeeds
        self._initialized = True

    async def get_me(self):
        """Mock get_me that always succeeds."""
        return self._me

    async def _post(self, *args, **kwargs):
        """Mock _post that always succeeds."""
        return self._me

    async def _do_post(self, *args, **kwargs):
        """Mock _do_post that always succeeds."""
        return self._me

    async def _make_request(self, *args, **kwargs):
        """Mock _make_request that always succeeds."""
        return self._me

    async def _initialize_request(self, *args, **kwargs):
        """Mock _initialize_request that always succeeds."""
        return self._me

    async def _validate_token(self, token: str) -> bool:
        """Mock token validation that always succeeds."""
        return True

    def __getattr__(self, name):
        """Mock any other attributes/methods that might be called."""
        return AsyncMock()

class MockApplication:
    """Mock Application class for testing."""
    def __init__(self, bot: MockBot):
        self.bot = bot
        bot._app = self
        self.handlers = [[]]  # Telegram bot uses a list of lists for handlers
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.shutdown = AsyncMock()
        self.initialize = AsyncMock()
        self.update_queue = AsyncMock()
        self.job_queue = AsyncMock()
        self.create_task = AsyncMock()

    async def add_handler(self, handler):
        """Add a handler to the application."""
        self.handlers[0].append(handler)

class MockApplicationBuilder:
    """Mock ApplicationBuilder for testing."""
    def __init__(self):
        self._token = None
        self._bot = None
        self._app = None

    def token(self, token: str):
        """Set the token and return self for chaining."""
        if not token:
            raise InvalidToken("Invalid token: You must pass the token you received from https://t.me/Botfather!")
        if token == "invalid_token":
            raise InvalidToken("Token validation failed")
        self._token = token
        self._bot = MockBot(token)
        return self

    def build(self):
        """Build and return the mock app."""
        if not self._token:
            raise RuntimeError("No bot token was set.")
        
        self._app = MockApplication(self._bot)
        return self._app

@pytest.fixture
def mock_telegram_bot(monkeypatch):
    """Create a mock telegram bot with application for testing."""
    builder = MockApplicationBuilder()
    builder.token("test_token")
    app = builder.build()
    
    # Patch the telegram classes
    monkeypatch.setattr("telegram.Bot", MockBot)
    monkeypatch.setattr("telegram.ext.ExtBot", MockBot)
    monkeypatch.setattr("telegram.ext.ApplicationBuilder", MockApplicationBuilder)
    monkeypatch.setattr("telegram.request.HTTPXRequest", MockHTTPXRequest)
    monkeypatch.setattr("chronicler.transports.telegram_bot_transport.ApplicationBuilder", MockApplicationBuilder)
    
    return app

def create_mock_telethon():
    """Create a mock Telethon client for user transport testing."""
    client = AsyncMock()
    
    # Mock basic client operations
    client.connect = AsyncMock()
    client.is_user_authorized = AsyncMock(return_value=True)
    client.start = AsyncMock()
    client.disconnect = AsyncMock()
    client.send_message = AsyncMock()
    client.send_file = AsyncMock()
    
    # Mock event registration
    event_handler = None
    def on_mock(event_type):
        nonlocal event_handler
        def register_handler(handler):
            nonlocal event_handler
            event_handler = handler
            # Create a simple async mock that stores the handler
            mock_handler = AsyncMock()
            mock_handler.__real_handler__ = handler
            return mock_handler
        return register_handler
    client.on = Mock(side_effect=on_mock)
    
    # Store event handler for testing
    client._event_handler = event_handler
    return client 