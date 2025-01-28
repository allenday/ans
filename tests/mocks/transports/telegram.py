"""Mock implementations for Telegram transports."""
import json
import time
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, call, MagicMock, patch
from typing import Optional, Tuple, Dict, Any, List, Union
from telegram.request import BaseRequest, RequestData
from telegram.error import InvalidToken

from chronicler.logging import get_logger

logger = get_logger(__name__)

class MockUpdate:
    """Mock Telegram Update object."""
    
    def __init__(self, message_text=None, chat_id=None, chat_title=None, 
                 sender_id=None, sender_name=None, message_id=None, thread_id=None):
        """Initialize mock update."""
        self.message = Mock()
        self.message.text = message_text
        self.message.chat = Mock()
        self.message.chat.id = chat_id or 123456789
        self.message.chat.title = chat_title or "Test Chat"
        self.message.chat.type = "private"
        self.message.from_user = Mock()
        self.message.from_user.id = sender_id or 987654321
        self.message.from_user.username = sender_name or "test_user"
        self.message.message_id = message_id or 1
        self.message.message_thread_id = thread_id
        self.message.date = Mock()
        self.message.date.timestamp = Mock(return_value=time.time())

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
        """Mock request wrapper that validates token."""
        if "invalid_token" in url:
            raise InvalidToken("Token validation failed")
        elif "test_token" in url:
            return json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()
        else:
            raise InvalidToken("Not Found")

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
        """Mock request that validates token."""
        if "invalid_token" in url:
            return 404, json.dumps({"ok": False, "error": "The token `invalid_token` was rejected by the server."}).encode()
        elif "test_token" in url:
            return 200, json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()
        else:
            return 404, json.dumps({"ok": False, "error": "Not Found"}).encode()

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
        """Mock post request that validates token."""
        if "invalid_token" in url:
            raise InvalidToken("The token `invalid_token` was rejected by the server.")
        elif "test_token" in url:
            return json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()
        else:
            raise InvalidToken("Not Found")

# Patch httpx.AsyncClient before any imports
class MockAsyncClient:
    def __init__(self, **kwargs):
        self.is_closed = False
        self.timeout = Mock(read=None, write=None, connect=None, pool=None)

    async def request(self, method, url, **kwargs):
        if "invalid_token" in url:
            return MockResponse(404, b'{"ok":false,"error_code":404,"description":"Not Found"}')
        elif "valid_token" in url:
            return MockResponse(200, b'{"ok":true,"result":{"id":123,"first_name":"Valid Bot","username":"valid_bot","can_join_groups":true,"can_read_all_group_messages":false,"supports_inline_queries":false,"is_bot":true}}')
        elif "test_token" in url:
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

from telegram.ext import ApplicationBuilder, CommandHandler, ExtBot, Application
from telegram.error import InvalidToken
from telegram.request import RequestData
from telegram import Bot, Message, Chat, PhotoSize, User
from collections import defaultdict

from chronicler.exceptions import (
    TransportError, 
    TransportAuthenticationError,
    TransportConnectionError,
    TransportMessageError
)
from chronicler.frames import CommandFrame
from chronicler.transports.events import EventMetadata
from chronicler.transports.telegram.transport.bot import TelegramBotTransport
from chronicler.transports.telegram_bot_event import TelegramBotEvent

from telegram.error import InvalidToken
from chronicler.exceptions import TransportError, TransportAuthenticationError

class MockBot:
    """Mock Telegram bot."""

    def __init__(self, token):
        """Initialize mock bot."""
        self.token = token
        self._message_id = 0
        self._command_handlers = {}
        self._initialized = False
        self.send_message = AsyncMock()
        self.send_photo = AsyncMock()
        self._request = [MockHTTPXRequest(), MockHTTPXRequest()]  # Bot uses two request objects
        self._app = None
        self.logger = get_logger(f"{__name__}.MockBot")

    async def initialize(self):
        """Initialize the bot.
        
        Raises:
            InvalidToken: If token is invalid
        """
        if not self._initialized:
            self.logger.debug("Initializing bot")
            await asyncio.gather(self._request[0].initialize(), self._request[1].initialize())
            if self.token == "invalid_token":
                raise InvalidToken("The token `invalid_token` was rejected by the server.")
            if not self.token:
                raise InvalidToken("Token must be provided")
            await self.get_me()  # This will validate the token
            self._initialized = True
            self.logger.debug("Bot initialized successfully")
        return True

    async def get_me(self):
        """Get bot info."""
        if not self._initialized and self.token != "test_token":
            # Special case for test_token to avoid initialization check
            raise InvalidToken("Bot must be initialized first")
        result = await self._request[0].post(f"https://api.telegram.org/bot{self.token}/getMe")
        return json.loads(result.decode())["result"]

    def _create_message(self, text, chat_id=None, message_id=None):
        """Create a mock message."""
        self._message_id += 1
        return {
            "message_id": message_id or self._message_id,
            "chat": {"id": chat_id or 123456789},
            "text": text,
            "date": int(time.time())
        }

    def _create_photo_message(self, photo_id, caption=None, chat_id=None, message_id=None):
        """Create a mock photo message."""
        self._message_id += 1
        return {
            "message_id": message_id or self._message_id,
            "chat": {"id": chat_id or 123456789},
            "photo": [{"file_id": photo_id}],
            "caption": caption,
            "date": int(time.time())
        }

    async def add_command_handler(self, command, handler):
        """Add a command handler."""
        if not command:
            raise ValueError("Command cannot be empty")
        if not handler:
            raise ValueError("Handler cannot be empty")
        self._command_handlers[command] = handler
        if self._app:
            await self._app.add_handler(CommandHandler(command, handler))

class MockApplication:
    """Mock Application class for testing."""

    def __init__(self):
        """Initialize mock application."""
        self.signal_handlers = []
        self.message_handlers = []
        self._initialized = False
        self._bot = None
        self.logger = get_logger(f"{__name__}.MockApplication")
        self.handlers = [[]]  # Initialize with an empty list for the first update handler group
        self._start = AsyncMock()  # Make start an AsyncMock
        self.stop = AsyncMock()  # Make stop an AsyncMock
        self.shutdown = AsyncMock()  # Make shutdown an AsyncMock

    @property
    def start(self):
        """Get the start method."""
        return self._start

    @start.setter
    def start(self, value):
        """Set the start method."""
        if not isinstance(value, AsyncMock):
            raise ValueError("start must be an AsyncMock")
        self._start = value

    @property
    def bot(self):
        """Get the bot instance."""
        return self._bot

    @bot.setter
    def bot(self, value):
        """Set the bot instance."""
        self._bot = value
        if value:
            value._app = self

    async def initialize(self):
        """Initialize the application."""
        self.logger.debug("Initializing application")
        if self._bot:
            await self._bot.initialize()
        self._initialized = True
        self.logger.info("Application initialized successfully")
        return True

    async def add_handler(self, handler, group=None):
        """Add a handler to the application."""
        self.logger.debug("Adding handler to application")
        if group is None:
            group = 0
        # Ensure we have enough groups
        while len(self.handlers) <= group:
            self.handlers.append([])
        self.handlers[group].append(handler)
        self.logger.debug("Handler added successfully")

    def add_signal_handler(self, signal, handler):
        """Add a signal handler to the application."""
        self.logger.debug(f"Adding signal handler for signal {signal}")
        self.signal_handlers.append((signal, handler))
        self.logger.debug("Signal handler added successfully")

class MockApplicationBuilder:
    """Mock application builder for testing."""
    def __init__(self):
        """Initialize builder."""
        self.logger = get_logger(f"{__name__}.MockApplicationBuilder")
        self._token = None
        self._bot = None
        
    def token(self, token: str) -> 'MockApplicationBuilder':
        """Set the bot token.
        
        Args:
            token: Bot token to use
            
        Raises:
            InvalidToken: If token is invalid
        """
        self.logger.debug(f"Setting token: {token}")
        if token == "invalid_token":
            self.logger.error("Invalid token provided")
            raise InvalidToken("Token validation failed")
            
        self._token = token
        return self
        
    def build(self) -> MockApplication:
        """Build and return a mock application.
        
        Returns:
            MockApplication instance
            
        Raises:
            TransportAuthenticationError: If token not set
        """
        self.logger.debug("Building application")
        if not self._token:
            self.logger.error("Token not set before building")
            raise TransportAuthenticationError("Token must be set before building")
            
        if not self._bot:
            self._bot = MockBot(self._token)
            
        app = MockApplication()
        app.bot = self._bot  # This will also set _app on the bot
        
        self.logger.info("Application built successfully")
        return app

@pytest.fixture
def mock_telegram_bot(monkeypatch):
    """Create a mock telegram bot with application for testing."""
    logger = get_logger(f"{__name__}.fixture")
    logger.debug("Setting up mock telegram bot")
    
    # Patch ApplicationBuilder and Application in the transport module
    monkeypatch.setattr('chronicler.transports.telegram.transport.bot.ApplicationBuilder', MockApplicationBuilder)
    monkeypatch.setattr('chronicler.transports.telegram.transport.bot.Application', MockApplication)
    
    stop_event = asyncio.Event()
    
    # Create transport
    transport = TelegramBotTransport("test_token")
    
    # Set up bot
    bot = MockBot("test_token")
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot._command_handlers = {}
    
    # Return all components
    return {
        'transport': transport,
        'bot': bot,
        'cmd_proc': AsyncMock(),
        'pipeline': AsyncMock(),
        'stop_event': stop_event,
    }

@pytest_asyncio.fixture
async def bot_transport(mock_telegram_bot, monkeypatch):
    """Create a bot transport instance."""
    # Patch the ApplicationBuilder and Application
    monkeypatch.setattr('chronicler.transports.telegram.transport.bot.ApplicationBuilder', MockApplicationBuilder)
    monkeypatch.setattr('chronicler.transports.telegram.transport.bot.Application', MockApplication)
    
    # Use real event loop for this test
    mock_telegram_bot['loop'] = asyncio.get_running_loop()
    transport = TelegramBotTransport(token="test_token")
    await transport.authenticate()  # This will initialize the bot properly
    
    # Set up message sender
    mock_sender = AsyncMock()
    mock_sender.send = AsyncMock()
    transport._message_sender = mock_sender
    
    return transport

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
    mock_transport._app = mock_telegram_bot['app']
    mock_transport._bot = mock_telegram_bot['app'].bot
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
    mock_pipeline.process = AsyncMock()

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