"""Tests for telegram bot transport."""
import pytest
from telegram.error import InvalidToken
from chronicler.exceptions import TransportError
from chronicler.logging import trace_operation, get_logger
from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from tests.mocks.fixtures import mock_telegram_bot
from tests.mocks.fixtures import assert_transport_error_async
from telegram.ext import CommandHandler
from unittest.mock import Mock, AsyncMock
from chronicler.transports.telegram_bot_update import TelegramBotUpdate
from chronicler.frames.media import TextFrame

logger = get_logger(__name__, component="test.transport")

@pytest.fixture
def assert_transport_error():
    """Fixture to assert that a TransportError is raised with expected message."""
    def _assert_transport_error(func, expected_message):
        error_caught = False
        try:
            func()
        except TransportError as e:
            error_caught = True
            assert str(e) == expected_message
        assert error_caught, f"Expected TransportError with message: {expected_message}"
    return _assert_transport_error

@pytest.fixture
def assert_empty_token_error():
    """Fixture to assert that empty token raises the expected error."""
    async def _assert_empty_token_error(transport):
        expected = "Invalid token: You must pass the token you received from https://t.me/Botfather!"
        error_caught = False
        try:
            await transport.authenticate()
        except TransportError as e:
            error_caught = True
            assert str(e) == expected
        assert error_caught, f"Expected TransportError with message: {expected}"
    return _assert_empty_token_error

def raise_transport_error(message: str):
    """Helper function that raises a TransportError."""
    raise TransportError(message)

def test_simple_error():
    """Test that we can catch a TransportError cleanly."""
    error_message = "test error"
    error_caught = False
    
    try:
        raise TransportError(error_message)
    except TransportError as e:
        error_caught = True
        assert str(e) == error_message
        
    assert error_caught

@trace_operation("test.simple.error.with.trace")
def test_simple_error_with_trace():
    """Test that we can catch a TransportError cleanly with trace logging."""
    error_message = "test error with trace"
    error_caught = False
    
    logger.info("Starting error test with trace")
    try:
        logger.debug("About to raise error")
        raise TransportError(error_message)
    except TransportError as e:
        logger.debug("Caught expected error")
        error_caught = True
        assert str(e) == error_message
    
    logger.info("Test completed successfully")    
    assert error_caught

def test_error_from_function():
    """Test catching an error raised from a function."""
    error_message = "error from function"
    error_caught = False
    
    try:
        raise_transport_error(error_message)
    except TransportError as e:
        error_caught = True
        assert str(e) == error_message
        
    assert error_caught

async def raise_empty_token_error():
    """Helper function that raises a TransportError for empty token."""
    raise TransportError("Invalid token: You must pass the token you received from https://t.me/Botfather!")

async def raise_invalid_token_error():
    """Helper function that raises a TransportError for invalid token."""
    raise TransportError("Invalid token: Token validation failed")

async def validate_empty_token():
    """Helper function that validates an empty token."""
    transport = TelegramBotTransport("")
    await transport.authenticate()
    return transport  # Return for post-error assertions

def test_transport_creation():
    """Test that creating a transport with empty token works."""
    transport = TelegramBotTransport("")
    assert not transport._initialized
    assert transport._token == ""

@pytest.mark.asyncio
async def test_empty_token_initial_state():
    """Test initial state of transport with empty token."""
    transport = TelegramBotTransport("")
    assert not transport._initialized
    assert transport._token == ""
    assert transport._app is None

@pytest.mark.asyncio 
async def test_empty_token_raises_error():
    """Test that empty token raises expected error during authentication."""
    transport = TelegramBotTransport("")
    expected_message = "Invalid token: You must pass the token you received from https://t.me/Botfather!"
    
    try:
        await transport.authenticate()
        pytest.fail("Expected TransportError was not raised")
    except TransportError as e:
        assert str(e) == expected_message

@pytest.mark.asyncio
async def test_empty_token_state_after_error():
    """Test transport state after authentication error with empty token."""
    transport = TelegramBotTransport("")
    try:
        await transport.authenticate()
    except TransportError:
        pass
        
    assert not transport._initialized
    assert transport._app is None

@pytest.mark.asyncio
async def test_authenticate_invalid_token(mock_telegram_bot):
    """Test that authenticating with invalid token raises expected error."""
    transport = TelegramBotTransport("invalid_token")
    expected = "Invalid token: Token validation failed"
    error_caught = False
    
    logger.debug("Starting invalid token test")
    try:
        logger.debug("Attempting to authenticate with invalid token")
        await transport.authenticate()
        logger.error("Expected TransportError was not raised")
        pytest.fail("Expected TransportError was not raised")
    except TransportError as e:
        logger.debug(f"Caught TransportError: {e}")
        error_caught = True
        assert str(e) == expected
    except Exception as e:
        logger.error(f"Caught unexpected error: {type(e)}: {e}")
        raise
    
    logger.debug("Verifying error was caught")
    assert error_caught, "Expected TransportError was not raised"
    
    logger.debug("Verifying transport state")
    assert not transport._initialized
    assert transport._app is None

@pytest.mark.asyncio
async def test_authenticate_valid_token(mock_telegram_bot):
    """Test that authenticating with valid token succeeds."""
    transport = TelegramBotTransport("valid_token")

    # Verify initial state
    assert not transport._initialized
    assert transport._token == "valid_token"
    assert transport._app is None

    # Attempt authentication
    await transport.authenticate()

    # Verify successful authentication
    assert transport._initialized
    assert transport._token == "valid_token"
    assert transport._app is not None
    assert transport._app.bot is not None
    assert transport._app.bot.token == "valid_token"
    assert transport._app.bot._initialized

@pytest.mark.asyncio
async def test_bot_initialization_after_auth(mock_telegram_bot):
    """Test that bot is properly initialized after successful authentication."""
    transport = TelegramBotTransport("valid_token")
    
    # First verify not initialized
    assert not transport._initialized
    assert transport._app is None
    
    # Authenticate
    await transport.authenticate()
    
    # Verify initialization state
    assert transport._initialized
    assert transport._app is not None
    assert transport._app.bot is not None
    assert transport._app.bot.token == "valid_token"

@pytest.mark.asyncio
async def test_command_registration_after_auth(mock_telegram_bot):
    """Test that commands can be registered after authentication."""
    transport = TelegramBotTransport("valid_token")
    await transport.authenticate()
    await transport.start()  # Start transport before registering commands
    
    # Register a test command
    async def test_command(frame):
        pass
    
    await transport.register_command("test", test_command)
    
    # Verify command was registered with leading slash in internal handlers
    assert "/test" in transport._command_handlers
    assert transport._command_handlers["/test"] == test_command
    
    # Verify command was added to application handlers without leading slash
    assert transport._app is not None
    logger.debug(f"App handlers: {transport._app.handlers[0]}")
    for handler in transport._app.handlers[0]:
        logger.debug(f"Handler type: {type(handler)}, commands: {getattr(handler, 'commands', None)}")
    
    assert any(isinstance(h, CommandHandler) and h.commands == frozenset(["test"])
              for h in transport._app.handlers[0])
    
    # Clean up
    await transport.stop()

@pytest.mark.asyncio
async def test_empty_token_minimal(mock_telegram_bot):
    """Test that empty token raises expected error during authentication."""
    # Create transport with empty token
    transport = TelegramBotTransport("")
    
    # Verify initial state
    assert not transport._initialized
    assert transport._token == ""
    assert transport._app is None
    
    # Attempt authentication and verify error
    expected = "Invalid token: You must pass the token you received from https://t.me/Botfather!"
    error_caught = False
    
    try:
        await transport.authenticate()
    except TransportError as e:
        error_caught = True
        assert str(e) == expected
    
    assert error_caught, "Expected TransportError was not raised"
    
    # Verify state after error
    assert not transport._initialized
    assert transport._app is None

@pytest.mark.asyncio
async def test_start_without_auth(mock_telegram_bot):
    """Test that starting without authentication raises error."""
    transport = TelegramBotTransport("valid_token")
    
    with pytest.raises(TransportError, match="Transport must be authenticated before starting"):
        await transport.start()

@pytest.mark.asyncio
async def test_start_error_handling(mock_telegram_bot):
    """Test error handling during start."""
    transport = TelegramBotTransport("valid_token")
    await transport.authenticate()
    
    # Make start() fail
    transport._app.start.side_effect = Exception("Failed to start")
    
    with pytest.raises(TransportError, match="Failed to start bot: Failed to start"):
        await transport.start()

@pytest.mark.asyncio
async def test_handle_message(mock_telegram_bot):
    """Test handling of incoming messages."""
    transport = TelegramBotTransport("valid_token")
    await transport.authenticate()
    await transport.start()
    
    # Create a mock update
    mock_update = Mock()
    mock_update.message = Mock()
    mock_update.message.text = "test message"
    mock_update.message.chat = Mock(id=123, title="Test Chat", type="private")
    mock_update.message.from_user = Mock(id=456, username="testuser")
    mock_update.message.message_id = 789
    
    # Track processed frames
    processed_frames = []
    transport.send = AsyncMock()
    transport.process_frame = AsyncMock(side_effect=lambda frame: processed_frames.append(frame) or frame)
    
    # Handle message
    await transport._handle_message(TelegramBotUpdate(mock_update))
    
    # Verify frame was processed and sent
    assert len(processed_frames) == 1
    frame = processed_frames[0]
    assert isinstance(frame, TextFrame)
    assert frame.content == "test message"
    assert frame.metadata["chat_id"] == 123
    assert frame.metadata["sender_id"] == 456
    transport.send.assert_called_once()

@pytest.mark.asyncio
async def test_handle_message_with_frame_processor(mock_telegram_bot):
    """Test message handling with custom frame processor."""
    transport = TelegramBotTransport("valid_token")
    await transport.authenticate()
    await transport.start()
    
    # Create a mock update
    mock_update = Mock()
    mock_update.message = Mock()
    mock_update.message.text = "test message"
    mock_update.message.chat = Mock(id=123, title="Test Chat", type="private")
    mock_update.message.from_user = Mock(id=456, username="testuser")
    mock_update.message.message_id = 789
    
    # Create frame processor that modifies content
    async def frame_processor(frame):
        frame.content = frame.content.upper()
        return frame
    
    transport.frame_processor = frame_processor
    transport.send = AsyncMock()
    
    # Handle message
    await transport._handle_message(TelegramBotUpdate(mock_update))
    
    # Verify frame was processed with uppercase content
    sent_frame = transport.send.call_args[0][0]
    assert isinstance(sent_frame, TextFrame)
    assert sent_frame.content == "TEST MESSAGE"

@pytest.mark.asyncio
async def test_handle_message_error(mock_telegram_bot):
    """Test error handling in message processing."""
    transport = TelegramBotTransport("valid_token")
    await transport.authenticate()
    await transport.start()
    
    # Create a mock update
    mock_update = Mock()
    mock_update.message = Mock()
    mock_update.message.text = "test message"
    mock_update.message.chat = Mock(id=123, title="Test Chat", type="private")
    mock_update.message.from_user = Mock(id=456, username="testuser")
    mock_update.message.message_id = 789
    
    # Make process_frame raise an error
    transport.process_frame = AsyncMock(side_effect=Exception("Process error"))
    transport.send = AsyncMock()
    
    # Handle message - should not raise but increment error count
    await transport._handle_message(TelegramBotUpdate(mock_update))
    assert transport._error_count == 1
    transport.send.assert_not_called()

@pytest.mark.asyncio
async def test_stop_without_auth(mock_telegram_bot):
    """Test stopping transport that wasn't authenticated."""
    transport = TelegramBotTransport("valid_token")
    await transport.stop()  # Should not raise
    assert not transport._initialized

@pytest.mark.asyncio
async def test_stop_after_auth(mock_telegram_bot):
    """Test stopping transport after authentication."""
    transport = TelegramBotTransport("valid_token")
    await transport.authenticate()
    await transport.start()
    
    await transport.stop()
    assert not transport._initialized
    transport._app.stop.assert_called_once()
    transport._app.shutdown.assert_called_once()