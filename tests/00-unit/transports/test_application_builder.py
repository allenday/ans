"""Tests for understanding ApplicationBuilder behavior."""
import pytest
from unittest.mock import AsyncMock, Mock, call, MagicMock
from telegram.ext import ApplicationBuilder, CommandHandler, ExtBot
from telegram.error import InvalidToken
from typing import Optional, Tuple, Dict
from telegram.request import RequestData, BaseRequest
import json
from telegram import Bot
import asyncio

from chronicler.exceptions import TransportError
from chronicler.transports.telegram.transport.bot import TelegramBotTransport

# Create a custom builder that returns our mock
class MockBuilder:
    """Mock ApplicationBuilder for testing."""
    def __init__(self):
        self._bot = AsyncMock()
        self._app = AsyncMock()
        self._token = None

    def token(self, token: str):
        """Set the token and return self for chaining."""
        self._token = token
        self._bot.token = token  # Set token on bot as well
        return self

    def build(self):
        """Build and return the mock app."""
        if not self._token:
            raise RuntimeError("No bot token was set.")
        
        # Set up bidirectional references
        self._app.bot = self._bot
        self._bot._app = self._app
        
        # Ensure start is an AsyncMock
        self._app.start = AsyncMock()
        
        return self._app

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

@pytest.mark.asyncio
async def test_application_builder_basic():
    """Test basic ApplicationBuilder functionality."""
    # Create a builder
    builder = ApplicationBuilder()
    
    # Set a valid token
    builder = builder.token("valid_token")
    
    # Build should return an Application instance
    app = builder.build()
    
    # Application should have basic attributes
    assert hasattr(app, "bot")
    assert hasattr(app, "start")
    assert app.bot.token == "valid_token"

@pytest.mark.asyncio
async def test_application_builder_methods():
    """Test that ApplicationBuilder methods are chainable and affect the built app."""
    builder = ApplicationBuilder()
    
    # Chain multiple configuration methods
    builder = (builder
              .token("valid_token")
              .concurrent_updates(True)
              .connection_pool_size(100))
    
    app = builder.build()
    assert app.bot.token == "valid_token"
    # Add assertions for other configured properties

@pytest.mark.asyncio
async def test_application_builder_invalid_token():
    """Test that ApplicationBuilder validates tokens."""
    builder = ApplicationBuilder()
    
    # Empty token should raise
    with pytest.raises(InvalidToken):
        builder = builder.token("")
        builder.build()
    
    # None token should raise
    with pytest.raises(InvalidToken):
        builder = builder.token(None)
        builder.build()
    
    # Build without token should raise RuntimeError
    with pytest.raises(RuntimeError, match="No bot token was set."):
        builder = ApplicationBuilder()
        builder.build()

@pytest.mark.asyncio
async def test_application_builder_mock_setup():
    """Test our understanding of how to properly mock ApplicationBuilder."""
    # Create mock bot and app
    mock_bot = AsyncMock()
    mock_bot.token = None
    mock_bot._initialized = False
    mock_bot._request = [MockHTTPXRequest(), MockHTTPXRequest()]  # Add mock request objects
    mock_bot.get_me = AsyncMock(return_value={
        "id": 123456789,
        "first_name": "Test Bot",
        "username": "test_bot",
        "can_join_groups": True,
        "can_read_all_group_messages": False,
        "supports_inline_queries": False
    })
    mock_bot.initialize = AsyncMock()  # Mock the initialize method

    mock_app = AsyncMock(spec=False)  # spec=False to allow __dict__ updates
    mock_app.bot = mock_bot
    mock_bot._app = mock_app
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Use the mock builder
    builder.token("test_token")
    app = builder.build()
    
    # Verify the mock setup
    assert app.bot.token == "test_token"
    assert isinstance(app.start, AsyncMock)  # This is key - start must be an AsyncMock
    
    # Test that we can set side effects
    app.start.side_effect = Exception("Test error")
    with pytest.raises(Exception, match="Test error"):
        await app.start()

@pytest.mark.asyncio
async def test_application_builder_start_error():
    """Test that we can properly handle start errors."""
    mock_bot = AsyncMock()
    mock_app = AsyncMock()
    mock_app.bot = mock_bot
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Set up the app with error on start
    builder.token("test_token")
    app = builder.build()
    
    # Verify start error handling
    app.start.side_effect = Exception("Failed to start")
    with pytest.raises(Exception, match="Failed to start"):
        await app.start()

@pytest.mark.asyncio
async def test_application_builder_handlers():
    """Test that we can add and use message handlers."""
    mock_bot = AsyncMock()
    mock_app = AsyncMock()
    mock_app.bot = mock_bot
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Set up the app
    builder.token("test_token")
    app = builder.build()
    
    # Add a message handler
    handler = AsyncMock()
    app.add_handler = AsyncMock()
    await app.add_handler(handler)
    
    # Verify handler was added
    app.add_handler.assert_called_once_with(handler)

@pytest.mark.asyncio
async def test_application_builder_stop():
    """Test that we can properly stop the application."""
    mock_bot = AsyncMock()
    mock_app = AsyncMock()
    mock_app.bot = mock_bot
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Set up the app
    builder.token("test_token")
    app = builder.build()
    
    # Start and stop the app
    await app.start()
    await app.stop()
    
    # Verify start and stop were called
    app.start.assert_called_once()
    app.stop.assert_called_once()

@pytest.mark.asyncio
async def test_application_builder_update_queue():
    """Test that we can properly handle the update queue."""
    mock_bot = AsyncMock()
    mock_app = AsyncMock()
    mock_app.bot = mock_bot
    
    # Create an update queue
    mock_queue = AsyncMock()
    mock_app.update_queue = mock_queue
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Set up the app
    builder.token("test_token")
    app = builder.build()
    
    # Verify we can get updates
    mock_update = AsyncMock()
    mock_queue.get.return_value = mock_update
    
    update = await app.update_queue.get()
    assert update == mock_update
    mock_queue.get.assert_called_once()

@pytest.mark.asyncio
async def test_application_builder_command_registration():
    """Test that we can register and handle commands."""
    mock_bot = AsyncMock()
    mock_app = AsyncMock()
    mock_app.bot = mock_bot
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Set up the app
    builder.token("test_token")
    app = builder.build()
    
    # Create a command handler
    async def command_callback(update, context):
        pass
    
    handler = CommandHandler("test", command_callback)
    await app.add_handler(handler)
    
    # Verify handler was added with correct command
    app.add_handler.assert_called_once_with(handler)
    assert isinstance(handler, CommandHandler)
    assert handler.commands == frozenset(["test"])  # Commands is a frozenset

@pytest.mark.asyncio
async def test_application_builder_message_processing():
    """Test that we can process messages and frames."""
    mock_bot = AsyncMock()
    mock_app = AsyncMock()
    mock_app.bot = mock_bot
    
    # Create an update queue
    mock_queue = AsyncMock()
    mock_app.update_queue = mock_queue
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Set up the app
    builder.token("test_token")
    app = builder.build()
    
    # Set up message handling
    message_handler = AsyncMock()
    app.add_handler = AsyncMock()
    await app.add_handler(message_handler)
    
    # Simulate message processing
    mock_update = AsyncMock()
    mock_update.message.text = "test message"
    mock_queue.get.return_value = mock_update
    
    # Process the update
    update = await app.update_queue.get()
    await message_handler(update, None)
    
    # Verify message was processed
    message_handler.assert_called_once_with(mock_update, None)
    mock_queue.get.assert_called_once()

@pytest.mark.asyncio
async def test_application_builder_initialization():
    """Test that app initialization sets up all required attributes."""
    mock_bot = AsyncMock()
    mock_bot.initialize = AsyncMock()
    mock_app = AsyncMock()
    mock_app.bot = mock_bot
    
    # Create required attributes
    mock_app.update_queue = AsyncMock()
    mock_app.job_queue = AsyncMock()
    mock_app.create_task = AsyncMock()
    
    # Set up initialize to call bot.initialize
    async def mock_initialize():
        await mock_bot.initialize()
    mock_app.initialize = AsyncMock(side_effect=mock_initialize)
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Set up the app
    builder.token("test_token")
    app = builder.build()
    
    # Verify all required attributes are set
    assert app.bot == mock_bot
    assert hasattr(app, "update_queue")
    assert hasattr(app, "job_queue")
    assert hasattr(app, "create_task")
    assert isinstance(app.start, AsyncMock)
    
    # Test initialization sequence
    await app.initialize()
    mock_bot.initialize.assert_called_once()
    
    # Verify app reference is set on bot
    assert mock_bot._app == app 

@pytest.mark.asyncio
async def test_application_builder_add_handler_behavior():
    """Test the specific behavior of add_handler to understand how it should be mocked."""
    # Create mock app and bot
    mock_bot = AsyncMock()
    mock_app = AsyncMock()
    mock_app.bot = mock_bot
    mock_bot._app = mock_app
    
    # Create builder with our mocks
    builder = MockBuilder()
    builder._bot = mock_bot
    builder._app = mock_app
    
    # Set up the app
    builder.token("test_token")
    app = builder.build()
    
    # Create add_handler as AsyncMock directly on app's dict
    add_handler_mock = AsyncMock(name="app.add_handler")
    app.__dict__["add_handler"] = add_handler_mock
    
    # Create a command handler
    async def command_callback(update, context):
        pass
    
    handler = CommandHandler("test", command_callback)
    
    # Add the handler
    await app.add_handler(handler)
    
    # Verify add_handler was called correctly
    add_handler_mock.assert_called_once_with(handler)
    
    # Verify we can set side effects
    add_handler_mock.reset_mock()
    add_handler_mock.side_effect = Exception("Failed to add handler")
    
    with pytest.raises(Exception, match="Failed to add handler"):
        await app.add_handler(handler)
    
    add_handler_mock.assert_called_once_with(handler)

@pytest.mark.asyncio
async def test_application_builder_transport_flow(monkeypatch):
    """Test our mock setup with the transport's authentication flow."""
    # Create a mock application builder that uses our MockBot
    class MockApplicationBuilder:
        def __init__(self):
            self._token = None

        def token(self, token: str):
            """Set the token and return self for chaining."""
            self._token = token
            return self

        def build(self):
            """Build and return the mock app."""
            if not self._token:
                raise RuntimeError("No bot token was set.")
            
            app = AsyncMock()
            bot = MockBot(self._token)
            app.bot = bot
            app.start = AsyncMock()

            # Make initialize actually call bot's initialize
            async def initialize():
                await bot.initialize()
                await bot.get_me()  # This will succeed because we've mocked get_me
            app.initialize = AsyncMock(side_effect=initialize)

            return app

    # Create a mock request that always returns success
    class MockRequest(BaseRequest):
        async def _request_wrapper(self, *args, **kwargs):
            return json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()

        async def do_request(self, *args, **kwargs):
            return 200, json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()

        async def initialize(self):
            pass

        async def shutdown(self):
            pass

        def parse_json_payload(self, payload: bytes) -> Dict:
            return json.loads(payload.decode())

        async def post(self, *args, **kwargs):
            return json.dumps({"ok": True, "result": {"id": 123456789, "is_bot": True, "first_name": "Test Bot", "username": "test_bot", "can_join_groups": True, "can_read_all_group_messages": True, "supports_inline_queries": False}}).encode()

    # Patch both the Bot and ApplicationBuilder classes
    monkeypatch.setattr("telegram.Bot", MockBot)
    monkeypatch.setattr("telegram.ext.ExtBot", MockBot)
    monkeypatch.setattr("telegram.ext.ApplicationBuilder", MockApplicationBuilder)
    monkeypatch.setattr("telegram.request.HTTPXRequest", MockRequest)
    monkeypatch.setattr("chronicler.transports.telegram.transport.bot.ApplicationBuilder", MockApplicationBuilder)

    # Create transport with test token
    transport = TelegramBotTransport("test_token")

    # Authenticate should succeed because our mock request always returns success
    await transport.authenticate()

    # Verify the transport is properly initialized
    assert transport._initialized is True
    assert transport._token == "test_token"
    assert transport._bot is not None 