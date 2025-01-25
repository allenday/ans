"""Mock implementations for Telegram transports."""
import pytest
from unittest.mock import AsyncMock, Mock, call, MagicMock, patch
from telegram.ext import ApplicationBuilder, CommandHandler, ExtBot, Application
from telegram.error import InvalidToken
from typing import Optional, Tuple, Dict, Any, List, Union
from telegram.request import RequestData, BaseRequest
import json
from telegram import Bot, Message, Chat, PhotoSize, User
import asyncio
from collections import defaultdict
import logging

from chronicler.exceptions import (
    TransportError, 
    TransportAuthenticationError,
    TransportConnectionError,
    TransportMessageError
)
from chronicler.frames import CommandFrame
from chronicler.transports.events import EventMetadata
from chronicler.transports.telegram_bot_transport import TelegramBotTransport, TelegramBotEvent
from chronicler.logging import get_logger

logger = get_logger(__name__)

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
    """Mock Bot class that simulates Telegram bot behavior."""
    def __init__(self, token: str = None):
        """Initialize bot with token."""
        self.token = token
        self._message_id = 0
        self.messages = []
        self._command_handlers = {}
        self.logger = get_logger(f"{__name__}.MockBot")
        
        # Set up AsyncMock methods
        self.send_message = AsyncMock()
        self.send_photo = AsyncMock()
        self.get_me = AsyncMock()
        
        # Configure return values
        self.get_me.return_value = {
            "id": 123456789,
            "is_bot": True,
            "first_name": "Test Bot",
            "username": "test_bot",
            "can_join_groups": True,
            "can_read_all_group_messages": True,
            "supports_inline_queries": False
        }

    def _create_message(self, chat_id: int = 123, text: str = "test", reply_to_message_id: int = None) -> Message:
        """Create a mock Message object."""
        self._message_id += 1
        chat = Chat(id=chat_id, type='private')
        message = Message(
            message_id=self._message_id,
            chat=chat,
            text=text,
            date=None,
            from_user=User(id=123, is_bot=True, first_name='Test Bot', username='test_bot')
        )
        self.messages.append(message)
        return message

    def _create_photo_message(self, chat_id: int = 123, caption: str = None, reply_to_message_id: int = None) -> Message:
        """Create a mock Message object with photo."""
        self._message_id += 1
        chat = Chat(id=chat_id, type='private')
        photo = [PhotoSize(file_id='test_photo_id', file_unique_id='test_unique_id', width=100, height=100)]
        message = Message(
            message_id=self._message_id,
            chat=chat,
            caption=caption,
            photo=photo,
            date=None,
            from_user=User(id=123, is_bot=True, first_name='Test Bot', username='test_bot')
        )
        self.messages.append(message)
        return message

    async def initialize(self) -> None:
        """Initialize the bot.
        
        Simulates validating the token and making an API call to get_me().
        
        Raises:
            InvalidToken: If token is invalid.
        """
        if self.token == "invalid_token":
            raise InvalidToken("Token validation failed")
            
        await self.get_me()

    async def add_command_handler(self, command: str, handler) -> None:
        """Add a command handler.
        
        Args:
            command: Command to handle (with or without leading /)
            handler: Async callback function to handle command
            
        Raises:
            ValueError: If command is empty or invalid
        """
        if not command:
            raise ValueError("Command cannot be empty")
            
        if not command.startswith('/'):
            command = '/' + command
            
        self.logger.debug(f"Registering handler for command: {command}")
        self._command_handlers[command] = handler

    async def handle_command(self, command: str, update: Any = None, context: Any = None) -> None:
        """Handle a command.
        
        Args:
            command: Command to handle (with or without leading /)
            update: Optional update object, will create default if None
            context: Optional context object
            
        Raises:
            KeyError: If command not registered
            TransportMessageError: If command execution fails
        """
        if not command.startswith('/'):
            command = '/' + command
            
        self.logger.debug(f"Handling command: {command}")
            
        if command not in self._command_handlers:
            self.logger.error(f"Command not registered: {command}")
            raise KeyError(f"Command {command} not registered")
            
        if update is None:
            update = self._create_message(text=command)
            
        try:
            await self._command_handlers[command](update, context)
            self.logger.debug(f"Successfully handled command: {command}")
        except Exception as e:
            self.logger.error(f"Failed to handle command {command}: {e}")
            raise TransportMessageError(f"Command execution failed: {e}")

class MockApplication:
    """Mock application for testing."""
    def __init__(self, bot: Optional['MockBot'] = None):
        """Initialize mock application."""
        self.bot = bot or MockBot()
        self.handlers = defaultdict(list)
        
        # Set up lifecycle methods as AsyncMock
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.shutdown = AsyncMock()
        self.add_handler = AsyncMock()

    async def initialize(self) -> None:
        """Initialize the application by initializing the bot."""
        await self.bot.initialize()
        self.bot._initialized = True  # Ensure bot is marked as initialized

class MockApplicationBuilder:
    """Mock application builder for testing."""
    def __init__(self):
        """Initialize builder."""
        self._token = None
        self._bot = None
        
    def token(self, token: str) -> 'MockApplicationBuilder':
        """Set the bot token.
        
        Args:
            token: Bot token to use
            
        Raises:
            InvalidToken: If token is invalid
        """
        if token == "invalid_token":
            raise InvalidToken("Token validation failed")
            
        self._token = token
        self._bot = MockBot(token)
        return self
        
    def build(self) -> MockApplication:
        """Build and return a mock application.
        
        Returns:
            MockApplication instance
            
        Raises:
            RuntimeError: If token not set
        """
        if not self._token:
            raise RuntimeError("Token must be set before building")
            
        return MockApplication(self._bot)

@pytest.fixture
def mock_telegram_bot(monkeypatch):
    """Create a mock telegram bot with application for testing.
    
    This fixture follows the same initialization sequence as the real bot:
    1. Create builder
    2. Set token
    3. Build application
    4. Initialize application (which initializes bot)
    """
    logger = get_logger(f"{__name__}.fixture")
    logger.debug("Setting up mock telegram bot")
    
    # Create and configure builder
    builder = MockApplicationBuilder()
    builder.token("test_token")
    
    # Build application and initialize it
    app = builder.build()
    app.bot._initialized = True  # Pre-initialize the bot since we're using a valid token
    
    # Create transport with the mock app
    transport = TelegramBotTransport(token="test_token")
    transport._app = app
    transport._bot = app.bot
    transport._initialized = True
    
    # Create other mocks
    storage = AsyncMock()
    cmd_proc = AsyncMock()
    pipeline = AsyncMock()
    stop_event = asyncio.Event()
    loop = MagicMock()
    
    # Mock the signal handler setup
    def mock_add_signal_handler(signum, callback):
        callback()
    loop.add_signal_handler = mock_add_signal_handler
    
    # Patch all the necessary classes
    monkeypatch.setattr("telegram.Bot", MockBot)
    monkeypatch.setattr("telegram.ext.ExtBot", MockBot)
    monkeypatch.setattr("telegram.ext.ApplicationBuilder", MockApplicationBuilder)
    monkeypatch.setattr("telegram.request.HTTPXRequest", MockHTTPXRequest)
    monkeypatch.setattr("chronicler.transports.telegram_bot_transport.ApplicationBuilder", MockApplicationBuilder)
    monkeypatch.setattr("chronicler.transports.telegram_bot_transport.TelegramBotTransport", lambda *args, **kwargs: transport)
    monkeypatch.setattr("chronicler.processors.storage_processor.StorageProcessor", lambda *args, **kwargs: storage)
    monkeypatch.setattr("chronicler.commands.processor.CommandProcessor", lambda *args, **kwargs: cmd_proc)
    monkeypatch.setattr("chronicler.pipeline.pipeline.Pipeline", lambda *args, **kwargs: pipeline)
    monkeypatch.setattr("asyncio.Event", lambda: stop_event)
    monkeypatch.setattr("asyncio.get_event_loop", lambda: loop)
    monkeypatch.setattr("signal.signal", lambda *args: None)
    
    logger.info("Mock telegram bot setup complete")
    
    # Return everything needed for testing
    return {
        'app': app,
        'transport': transport,
        'storage': storage,
        'cmd_proc': cmd_proc,
        'pipeline': pipeline,
        'stop_event': stop_event,
        'loop': loop
    }

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