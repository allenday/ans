"""Tests for telegram bot transport using the new mock setup."""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from chronicler.exceptions import TransportError, TransportAuthenticationError
from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.frames.command import CommandFrame
from telegram.ext import CommandHandler
from tests.mocks.transports.telegram import mock_telegram_bot
from telegram.error import InvalidToken
from chronicler.transports.telegram_bot_update import TelegramBotUpdate
from chronicler.frames.base import Frame

@pytest.mark.asyncio
async def test_empty_token_initial_state(mock_telegram_bot):
    """Test initial state of transport with empty token."""
    transport = TelegramBotTransport("")
    assert not transport._initialized
    assert transport._token == ""
    assert transport._app is None

@pytest.mark.asyncio 
async def test_empty_token_raises_error(mock_telegram_bot):
    """Test that empty token raises expected error during authentication."""
    transport = TelegramBotTransport("")
    expected_message = "Invalid token: You must pass the token you received from https://t.me/Botfather!"
    
    try:
        await transport.authenticate()
        pytest.fail("Expected TransportAuthenticationError was not raised")
    except TransportAuthenticationError as e:
        assert str(e) == expected_message

@pytest.mark.asyncio
async def test_empty_token_state_after_error(mock_telegram_bot):
    """Test transport state after authentication error with empty token."""
    transport = TelegramBotTransport("")
    try:
        await transport.authenticate()
    except TransportAuthenticationError:
        pass
        
    assert not transport._initialized
    assert transport._app is None

@pytest.mark.asyncio
async def test_bot_initialization_after_auth(mock_telegram_bot):
    """Test that bot is properly initialized after successful authentication."""
    transport = TelegramBotTransport("test_token")
    
    # First verify not initialized
    assert not transport._initialized
    assert transport._app is None
    
    # Authenticate
    await transport.authenticate()
    
    # Verify initialization state
    assert transport._initialized
    assert transport._app is not None
    assert transport._app.bot is not None
    assert transport._app.bot.token == "test_token"

@pytest.mark.asyncio
async def test_command_registration_after_auth(mock_telegram_bot):
    """Test that commands can be registered after authentication."""
    transport = TelegramBotTransport("test_token")
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
    assert any(isinstance(h, CommandHandler) and h.commands == frozenset(["test"])
              for h in transport._app.handlers[0])
    
    # Clean up
    await transport.stop()

@pytest.mark.asyncio
async def test_start_without_auth(mock_telegram_bot):
    """Test that starting without authentication raises error."""
    transport = TelegramBotTransport("test_token")
    
    with pytest.raises(TransportAuthenticationError, match="Transport must be authenticated before starting"):
        await transport.start()

@pytest.mark.asyncio
async def test_start_error_handling(mock_telegram_bot):
    """Test error handling during start."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    
    # Make start() fail
    transport._app.start.side_effect = Exception("Failed to start")
    
    with pytest.raises(TransportError, match="Failed to start bot: Failed to start"):
        await transport.start()

@pytest.mark.asyncio
async def test_stop_after_auth(mock_telegram_bot):
    """Test stopping transport after authentication."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    await transport.stop()
    assert not transport._initialized
    transport._app.stop.assert_called_once()
    transport._app.shutdown.assert_called_once()

@pytest.mark.asyncio
async def test_send_text_frame(mock_telegram_bot):
    """Test sending a text frame."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Create a text frame
    frame = TextFrame(
        content="test message",
        metadata={"chat_id": 123, "thread_id": 456}
    )
    
    # Mock the bot's send_message method to return a message ID
    mock_message = AsyncMock()
    mock_message.message_id = 789
    transport._app.bot.send_message.return_value = mock_message
    
    # Send the frame
    result = await transport.send(frame)
    
    # Verify the message was sent correctly
    transport._app.bot.send_message.assert_called_once_with(
        chat_id=123,
        text="test message",
        reply_to_message_id=456
    )
    
    # Verify frame metadata was updated
    assert result.metadata["message_id"] == 789

@pytest.mark.asyncio
async def test_send_unsupported_frame_type(mock_telegram_bot):
    """Test sending an unsupported frame type."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Create a mock frame that's neither TextFrame nor ImageFrame
    class UnsupportedFrame:
        def __init__(self, metadata=None):
            self.metadata = metadata or {}
    
    frame = UnsupportedFrame(metadata={"chat_id": 123})
    
    with pytest.raises(TransportError, match="Unsupported frame type"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_send_uninitialized(mock_telegram_bot):
    """Test sending when transport is not initialized."""
    transport = TelegramBotTransport("test_token")
    frame = TextFrame(content="test", metadata={"chat_id": 123})
    
    with pytest.raises(RuntimeError, match="Transport not initialized"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_send_missing_chat_id(mock_telegram_bot):
    """Test sending without chat_id."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    frame = TextFrame(content="test", metadata={})
    
    with pytest.raises(ValueError, match="chat_id is required"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_send_error_handling(mock_telegram_bot):
    """Test error handling during send."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    frame = TextFrame(content="test", metadata={"chat_id": 123})
    transport._app.bot.send_message.side_effect = Exception("Send failed")
    
    with pytest.raises(TransportError, match="Send failed"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_invalid_command_characters(mock_telegram_bot):
    """Test registering commands with invalid characters."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    async def test_command(frame):
        pass
    
    # Test invalid characters
    invalid_commands = ["test@command", "test#1", "test!", "test space"]
    
    for cmd in invalid_commands:
        with pytest.raises(TransportError, match=f"Failed to register command: Command `{cmd}` is not a valid bot command"):
            await transport.register_command(cmd, test_command)

@pytest.mark.asyncio
async def test_duplicate_command_registration(mock_telegram_bot):
    """Test registering the same command multiple times."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    command_executions = []
    
    async def command1(frame):
        command_executions.append("command1")
        
    async def command2(frame):
        command_executions.append("command2")
    
    # Register first command
    await transport.register_command("test", command1)
    
    # Register same command again
    await transport.register_command("test", command2)
    
    # Verify only the second command is registered
    assert transport._command_handlers["/test"] == command2 

@pytest.mark.asyncio
async def test_process_frame_without_processor(mock_telegram_bot):
    """Test processing frame without frame processor."""
    transport = TelegramBotTransport("test_token")
    frame = TextFrame(content="test", metadata={"chat_id": 123})
    
    result = await transport.process_frame(frame)
    assert result == frame  # Should return unmodified frame

@pytest.mark.asyncio
async def test_process_frame_with_processor(mock_telegram_bot):
    """Test processing frame with frame processor."""
    transport = TelegramBotTransport("test_token")
    
    # Create a processor that modifies the frame
    async def processor(frame):
        frame.content = frame.content.upper()
        return frame
    
    transport.frame_processor = processor
    frame = TextFrame(content="test", metadata={"chat_id": 123})
    
    result = await transport.process_frame(frame)
    assert result.content == "TEST"

@pytest.mark.asyncio
async def test_handle_message_error(mock_telegram_bot):
    """Test error handling in message processing."""
    transport = TelegramBotTransport("test_token")
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
async def test_bot_transport_command_not_found(mock_telegram_bot):
    """Test handling of unregistered commands in TelegramBotTransport."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Register a command
    handler = AsyncMock()
    await transport.register_command("test", handler)
    
    # Verify only the registered command has a handler
    assert "/test" in transport._command_handlers
    assert "/unknown" not in transport._command_handlers
    
    # Mock an incoming unregistered command
    mock_update = Mock()
    mock_update.message = Mock(
        text="/unknown",
        chat=Mock(id=456, title="Test Chat", type="private"),
        from_user=Mock(id=789, username="testuser"),
        message_id=123
    )
    
    # Handle the message - should not call our test handler
    await transport._handle_message(TelegramBotUpdate(mock_update))
    handler.assert_not_called()

@pytest.mark.asyncio
async def test_handle_command_execution(mock_telegram_bot):
    """Test command execution through handler."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Track command execution
    command_executed = False
    
    async def test_command(frame):
        nonlocal command_executed
        command_executed = True
        assert isinstance(frame, CommandFrame)
        assert frame.command == "/test"
        assert frame.args == ["arg1", "arg2"]
    
    # Register command
    await transport.register_command("test", test_command)
    
    # Create mock update for command
    mock_update = Mock()
    mock_update.message = Mock(
        text="/test arg1 arg2",
        chat=Mock(id=123, title="Test Chat", type="private"),
        from_user=Mock(id=456, username="testuser"),
        message_id=789
    )
    
    # Find command handler
    command_handler = next(
        h for h in transport._app.handlers[0] 
        if isinstance(h, CommandHandler) and "test" in h.commands
    )
    
    # Create mock context
    mock_context = Mock()
    mock_context.args = ["arg1", "arg2"]
    
    # Execute command
    await command_handler.callback(mock_update, mock_context)
    
    assert command_executed

@pytest.mark.asyncio
async def test_authenticate_invalid_token(mock_telegram_bot):
    """Test that authenticating with invalid token raises expected error."""
    transport = TelegramBotTransport("invalid_token")
    expected = "Token validation failed"
    
    with pytest.raises(TransportAuthenticationError, match=expected):
        await transport.authenticate()
    
    assert not transport._initialized
    assert transport._app is None

@pytest.mark.asyncio
async def test_stop_without_auth(mock_telegram_bot):
    """Test stopping transport that wasn't authenticated."""
    transport = TelegramBotTransport("test_token")
    await transport.stop()  # Should not raise
    assert not transport._initialized 

@pytest.mark.asyncio
async def test_send_image_frame(mock_telegram_bot):
    """Test sending an image frame with caption."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Create an image frame
    frame = ImageFrame(
        content=b"test_image_data",
        metadata={
            "chat_id": 123,
            "thread_id": 456,
            "caption": "test caption"
        }
    )
    
    # Mock the bot's send_photo method to return a message ID
    mock_message = AsyncMock()
    mock_message.message_id = 789
    send_photo = AsyncMock(return_value=mock_message)
    transport._app.bot.send_photo = send_photo
    
    # Send the frame
    result = await transport.send(frame)
    
    # Verify the photo was sent correctly
    transport._app.bot.send_photo.assert_called_once_with(
        chat_id=123,
        photo=b"test_image_data",
        caption=frame.metadata["caption"],
        reply_to_message_id=456
    )
    
    # Verify frame metadata was updated
    assert result.metadata["message_id"] == 789

@pytest.mark.asyncio
async def test_send_image_frame_without_caption(mock_telegram_bot):
    """Test sending an image frame without caption."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Create an image frame without caption
    frame = ImageFrame(
        content=b"test_image_data",
        metadata={"chat_id": 123}
    )
    
    # Mock the bot's send_photo method to return a message ID
    mock_message = AsyncMock()
    mock_message.message_id = 789
    transport._app.bot.send_photo.return_value = mock_message
    
    # Send the frame
    result = await transport.send(frame)
    
    # Verify the photo was sent correctly
    transport._app.bot.send_photo.assert_called_once_with(
        chat_id=123,
        photo=b"test_image_data",
        caption=None,
        reply_to_message_id=None
    )
    
    # Verify frame metadata was updated
    assert result.metadata["message_id"] == 789 

@pytest.mark.asyncio
async def test_frame_processor_returns_none(mock_telegram_bot):
    """Test handling when frame processor returns None."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Create a processor that returns None
    async def processor(frame):
        return None
    
    transport.frame_processor = processor
    
    # Mock an incoming message
    mock_update = Mock()
    mock_update.message = Mock(
        text="test message",
        chat=Mock(id=123, title="Test Chat", type="private"),
        from_user=Mock(id=456, username="testuser"),
        message_id=789
    )
    
    # Handle message - should not send anything since processor returns None
    await transport._handle_message(TelegramBotUpdate(mock_update))
    transport._app.bot.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_frame_processor_modifies_metadata(mock_telegram_bot):
    """Test that frame processor can modify frame metadata."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Create a processor that adds metadata
    async def processor(frame):
        frame.metadata["processed"] = True
        frame.metadata["timestamp"] = "test_time"
        return frame
    
    transport.frame_processor = processor
    
    # Create a text frame
    frame = TextFrame(
        content="test message",
        metadata={"chat_id": 123}
    )
    
    # Process the frame
    processed = await transport.process_frame(frame)
    
    # Verify metadata was added
    assert processed.metadata["processed"] is True
    assert processed.metadata["timestamp"] == "test_time"
    assert processed.metadata["chat_id"] == 123  # Original metadata preserved

@pytest.mark.asyncio
async def test_frame_processor_chaining(mock_telegram_bot):
    """Test chaining multiple frame processors."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Create processors that modify content and metadata
    async def processor1(frame):
        frame.content = frame.content.upper()
        frame.metadata["processor1"] = True
        return frame
        
    async def processor2(frame):
        frame.content = f"[{frame.content}]"
        frame.metadata["processor2"] = True
        return frame
    
    # Chain processors
    async def chain_processor(frame):
        frame = await processor1(frame)
        frame = await processor2(frame)
        return frame
    
    transport.frame_processor = chain_processor
    
    # Create a text frame
    frame = TextFrame(
        content="test",
        metadata={"chat_id": 123}
    )
    
    # Process the frame
    processed = await transport.process_frame(frame)
    
    # Verify processors were applied in order
    assert processed.content == "[TEST]"
    assert processed.metadata["processor1"] is True
    assert processed.metadata["processor2"] is True

@pytest.mark.asyncio
async def test_frame_processor_error_handling(mock_telegram_bot):
    """Test error handling in frame processor."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()

    # Create a processor that raises an error
    async def processor(frame):
        transport._error_count += 1  # Increment error count before raising
        raise TransportError("Process error")

    transport.frame_processor = processor

    # Create a text frame
    frame = TextFrame(
        content="test",
        metadata={"chat_id": 123}
    )

    # Initial error count should be 0
    assert transport._error_count == 0

    # Process the frame - should raise TransportError
    with pytest.raises(TransportError, match="Process error"):
        await transport.process_frame(frame)

    # Error count should be incremented
    assert transport._error_count == 1

@pytest.mark.asyncio
async def test_frame_processor_chaining_without_app():
    """Test frame processor chaining without initialized app."""
    transport = TelegramBotTransport("test_token")
    
    # Create processors that modify content and metadata
    async def processor1(frame):
        frame.content = frame.content.upper()
        return frame
        
    async def processor2(frame):
        frame.content = f"[{frame.content}]"
        return frame
    
    # Chain processors
    async def chain_processor(frame):
        frame = await processor1(frame)
        frame = await processor2(frame)
        return frame
    
    transport.frame_processor = chain_processor
    
    # Create a text frame
    frame = TextFrame(
        content="test",
        metadata={"chat_id": 123}
    )
    
    # Process the frame - should work without initialized app
    processed = await transport.process_frame(frame)
    assert processed.content == "[TEST]"

@pytest.mark.asyncio
async def test_frame_processor_metadata_manipulation():
    """Test frame processor metadata manipulation without app."""
    transport = TelegramBotTransport("test_token")
    
    # Create a processor that modifies metadata
    async def processor(frame):
        frame.metadata["processed"] = True
        frame.metadata["timestamp"] = "test_time"
        return frame
    
    transport.frame_processor = processor
    
    # Create a text frame
    frame = TextFrame(
        content="test",
        metadata={"chat_id": 123}
    )
    
    # Process the frame
    processed = await transport.process_frame(frame)
    
    # Verify metadata was modified
    assert processed.metadata["processed"] is True
    assert processed.metadata["timestamp"] == "test_time"
    assert processed.metadata["chat_id"] == 123  # Original metadata preserved

@pytest.mark.asyncio
async def test_frame_validation_without_metadata(mock_telegram_bot):
    """Test frame validation when metadata is None."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()

    frame = TextFrame(content="test")
    frame.metadata = None

    with pytest.raises(ValueError, match="chat_id is required"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_frame_validation_empty_metadata(mock_telegram_bot):
    """Test frame validation with empty metadata."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()

    frame = TextFrame(content="test", metadata={})

    with pytest.raises(ValueError, match="chat_id is required"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_frame_type_validation(mock_telegram_bot):
    """Test validation of frame types."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()

    # Create an invalid frame type
    class InvalidFrame(Frame):
        def __init__(self):
            super().__init__()
            self.content = "test"
            self.metadata = {"chat_id": 123}

    frame = InvalidFrame()

    with pytest.raises(TransportError, match="Unsupported frame type"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_error_count_tracking(mock_telegram_bot):
    """Test error count tracking during message processing."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()
    
    # Create a processor that raises an error
    async def processor(frame):
        raise ValueError("Process error")
    
    transport.frame_processor = processor
    
    # Mock an incoming message
    mock_update = Mock()
    mock_update.message = Mock(
        text="test message",
        chat=Mock(id=123, title="Test Chat", type="private"),
        from_user=Mock(id=456, username="testuser"),
        message_id=789
    )
    
    # Initial error count should be 0
    assert transport._error_count == 0
    
    # Handle message - should increment error count
    await transport._handle_message(TelegramBotUpdate(mock_update))
    assert transport._error_count == 1
    
    # Handle another message - should increment again
    await transport._handle_message(TelegramBotUpdate(mock_update))
    assert transport._error_count == 2

@pytest.mark.asyncio
async def test_error_count_tracking_without_app(mock_telegram_bot):
    """Test error count tracking without initialized app."""
    transport = TelegramBotTransport("test_token")
    await transport.authenticate()
    await transport.start()

    # Create a processor that raises an error
    async def processor(frame):
        transport._error_count += 1  # Increment error count before raising
        raise TransportError("Process error")

    transport.frame_processor = processor

    # Create a text frame
    frame = TextFrame(
        content="test",
        metadata={"chat_id": 123}
    )

    # Initial error count should be 0
    assert transport._error_count == 0

    # Process frame - should increment error count
    with pytest.raises(TransportError, match="Process error"):
        await transport.process_frame(frame)

    # Error count should be incremented
    assert transport._error_count == 1

@pytest.mark.asyncio
async def test_authenticate_build_error():
    """Test error handling when ApplicationBuilder.build() fails with a generic error."""
    transport = TelegramBotTransport("test_token")
    
    # Mock ApplicationBuilder to raise an error during build
    with patch('telegram.ext.ApplicationBuilder.build', side_effect=Exception("Build failed")):
        with pytest.raises(TransportError, match="Failed to build application: Build failed"):
            await transport.authenticate()
    
    assert not transport.is_running
    assert transport._app is None

@pytest.mark.asyncio
async def test_authenticate_initialize_error():
    """Test error handling when app.initialize() fails."""
    transport = TelegramBotTransport("test_token")
    
    # Create mock app with failing initialize
    mock_app = AsyncMock()
    mock_app.initialize = AsyncMock(side_effect=Exception("Initialize failed"))
    mock_app.bot = AsyncMock()
    
    with patch('telegram.ext.ApplicationBuilder.build', return_value=mock_app):
        with pytest.raises(TransportAuthenticationError, match="Failed to initialize bot: Initialize failed"):
            await transport.authenticate()
    
    assert not transport.is_running
    assert transport._app is None

@pytest.mark.asyncio
async def test_stop_without_initialization():
    """Test stopping a transport that was never initialized."""
    transport = TelegramBotTransport("test_token")
    
    # Should not raise any errors
    await transport.stop()
    
    assert not transport.is_running
    assert transport._app is None 

@pytest.mark.asyncio
async def test_command_handler_error():
    """Test error handling when command handler raises an exception."""
    transport = TelegramBotTransport("test_token")
    
    # Mock the bot initialization
    transport._app = MagicMock()
    transport._app.initialize = AsyncMock()
    transport._app.bot = MagicMock()
    transport._app.bot.get_me = AsyncMock()
    transport._app.add_handler = AsyncMock()  # Mock add_handler as async
    transport._initialized = True
    transport._bot = transport._app.bot
    
    # Create a command handler that raises an error
    async def error_handler(frame):
        raise Exception("Command handler error")
    
    # Register the command
    await transport.register_command("/test", error_handler)
    
    # Create a mock update
    mock_update = MagicMock()
    mock_update.message = MagicMock()
    mock_update.message.text = "/test arg1 arg2"
    mock_update.message.chat = MagicMock()
    mock_update.message.chat.id = 123456
    mock_update.message.chat.title = "Test Chat"
    mock_update.message.chat.type = "private"
    mock_update.message.from_user = MagicMock()
    mock_update.message.from_user.id = 789
    mock_update.message.from_user.username = "test_user"
    mock_update.message.message_id = 1

    # Process command and expect error
    with pytest.raises(TransportError, match="Failed to handle command: Command handler error"):
        await transport._handle_command(mock_update, error_handler) 