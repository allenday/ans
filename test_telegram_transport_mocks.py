"""Mock tests for Telegram transports."""
import pytest
from unittest.mock import AsyncMock, Mock, patch, call
from telegram.ext import CommandHandler
from telethon import events

from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame
from chronicler.frames.command import CommandFrame
from chronicler.transports.telegram_factory import (
    TelegramUserTransport,
    TelegramBotTransport
)

@pytest.fixture
def mock_telethon():
    """Mock Telethon client with async methods."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock:
        client = Mock()
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
                return handler
            return register_handler
        client.on = Mock(side_effect=on_mock)
        mock.return_value = client
        
        # Store event handler for testing
        mock.event_handler = lambda: event_handler
        yield mock

@pytest.fixture
def mock_events():
    """Mock Telethon events."""
    with patch('chronicler.transports.telegram_factory.events') as mock:
        def new_message_mock(pattern=None):
            event = Mock()
            event.pattern = pattern
            return event
        mock.NewMessage = Mock(side_effect=new_message_mock)
        yield mock

@pytest.fixture
def mock_telegram_bot():
    """Mock python-telegram-bot with async methods."""
    with patch('chronicler.transports.telegram_factory.Application') as mock:
        app = Mock()
        app.initialize = AsyncMock()
        app.start = AsyncMock()
        app.stop = AsyncMock()
        app.updater = Mock()
        app.updater.start_polling = AsyncMock()
        app.updater.stop = AsyncMock()
        app.bot = Mock()
        app.bot.send_message = AsyncMock()
        app.bot.send_photo = AsyncMock()
        app.bot.send_document = AsyncMock()
        
        # Mock command handler registration
        command_handler = None
        def add_handler_mock(handler):
            nonlocal command_handler
            command_handler = handler
        app.add_handler = Mock(side_effect=add_handler_mock)
        
        builder = Mock()
        builder.token = Mock(return_value=Mock(build=Mock(return_value=app)))
        mock.builder = Mock(return_value=builder)
        
        # Store command handler for testing
        mock.command_handler = lambda: command_handler
        yield mock

@pytest.mark.asyncio
async def test_user_transport_command_registration(mock_telethon, mock_events):
    """Test command registration in TelegramUserTransport."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    # Mock command handler
    handler = AsyncMock()
    await transport.register_command("test", handler)
    
    # Verify handler was registered
    assert "/test" in transport._command_handlers
    assert transport._command_handlers["/test"] == handler
    
    # Start transport to register event handler
    await transport.start()
    
    # Get the registered event handler
    event_handler = mock_telethon.event_handler()
    assert event_handler is not None, "Command event handler not registered"
    
    # Mock an incoming command
    mock_event = Mock()
    mock_event.message = Mock(text="/test arg1 arg2", id=123)
    mock_event.chat_id = 456
    mock_event.chat = Mock(title="Test Chat")
    mock_event.sender_id = 789
    mock_event.sender = Mock(username="testuser")
    
    # Trigger the event handler
    await event_handler(mock_event)
    
    # Verify handler was called with correct frame
    handler.assert_called_once()
    frame = handler.call_args[0][0]
    assert isinstance(frame, CommandFrame)
    assert frame.command == "/test"
    assert frame.args == ["arg1", "arg2"]
    assert frame.metadata['chat_id'] == 456
    assert frame.metadata['sender_id'] == 789

@pytest.mark.asyncio
async def test_bot_transport_command_registration(mock_telegram_bot):
    """Test command registration in TelegramBotTransport."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    app = mock_telegram_bot.builder().token().build()
    
    # Mock command handler
    handler = AsyncMock()
    await transport.register_command("test", handler)
    
    # Verify handler was registered
    assert "/test" in transport._command_handlers
    assert transport._command_handlers["/test"] == handler
    
    # Get the registered command handler
    command_handler = mock_telegram_bot.command_handler()
    assert command_handler is not None, "Command handler not registered"
    assert isinstance(command_handler, CommandHandler)
    assert command_handler.commands == ["test"]
    
    # Mock an incoming command
    mock_update = Mock()
    mock_update.message = Mock(
        text="/test arg1 arg2",
        message_id=123,
        chat_id=456,
        chat=Mock(title="Test Chat")
    )
    mock_update.message.from_user = Mock(
        id=789,
        username="testuser",
        first_name="Test User"
    )
    
    mock_context = Mock(args=["arg1", "arg2"])
    
    # Trigger the command handler
    await command_handler.callback(mock_update, mock_context)
    
    # Verify handler was called with correct frame
    handler.assert_called_once()
    frame = handler.call_args[0][0]
    assert isinstance(frame, CommandFrame)
    assert frame.command == "/test"
    assert frame.args == ["arg1", "arg2"]
    assert frame.metadata['chat_id'] == 456
    assert frame.metadata['sender_id'] == 789

@pytest.mark.asyncio
async def test_user_transport_command_not_found(mock_telethon, mock_events):
    """Test handling of unregistered commands in TelegramUserTransport."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    # Start transport to register event handler
    await transport.start()
    
    # Get the registered event handler
    event_handler = mock_telethon.event_handler()
    assert event_handler is not None, "Command event handler not registered"
    
    # Mock an incoming unregistered command
    mock_event = Mock()
    mock_event.message = Mock(text="/unknown", id=123)
    mock_event.chat_id = 456
    mock_event.chat = Mock(title="Test Chat")
    mock_event.sender_id = 789
    mock_event.sender = Mock(username="testuser")
    
    # Trigger the event handler - should not raise any errors
    await event_handler(mock_event)

@pytest.mark.asyncio
async def test_bot_transport_command_not_found(mock_telegram_bot):
    """Test handling of unregistered commands in TelegramBotTransport."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    app = mock_telegram_bot.builder().token().build()
    
    # Register a command
    handler = AsyncMock()
    await transport.register_command("test", handler)
    
    # Verify only the registered command has a handler
    assert "/test" in transport._command_handlers
    assert "/unknown" not in transport._command_handlers
    
    # Get the command handler
    command_handler = mock_telegram_bot.command_handler()
    assert command_handler is not None, "Command handler not registered"
    assert isinstance(command_handler, CommandHandler)
    assert command_handler.commands == ["test"]
    
    # Mock an incoming unregistered command
    mock_update = Mock()
    mock_update.message = Mock(
        text="/unknown",
        message_id=123,
        chat_id=456,
        chat=Mock(title="Test Chat")
    )
    mock_update.message.from_user = Mock(
        id=789,
        username="testuser"
    )
    
    mock_context = Mock(args=[])
    
    # Trigger the command handler - should not call our test handler
    await command_handler.callback(mock_update, mock_context)
    handler.assert_not_called() 