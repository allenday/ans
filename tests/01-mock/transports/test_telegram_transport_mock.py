"""Mock tests for Telegram transports."""
import pytest
from unittest.mock import AsyncMock, Mock, patch, call
from telegram.ext import CommandHandler, Application
from telethon import events

from chronicler.frames import TextFrame, ImageFrame, DocumentFrame, CommandFrame
from chronicler.transports.telegram_factory import (
    TelegramUserTransport,
    TelegramBotTransport
)
from chronicler.transports.events import TelegramBotEvent, EventMetadata

@pytest.fixture
def mock_telethon():
    """Mock Telethon client."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock:
        client = AsyncMock()
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
        mock.return_value = client
        
        # Store event handler for testing
        mock.event_handler = lambda: event_handler
        yield mock

@pytest.fixture
def mock_telegram_bot():
    """Mock python-telegram-bot with async methods."""
    with patch('chronicler.transports.telegram_factory.Application') as mock:
        app = AsyncMock()
        app.initialize = AsyncMock()
        app.start = AsyncMock()
        app.stop = AsyncMock()
        app.updater = AsyncMock()
        app.updater.start_polling = AsyncMock()
        app.updater.stop = AsyncMock()
        app.bot = AsyncMock()
        app.bot.send_message = AsyncMock()
        app.bot.send_photo = AsyncMock()
        app.bot.send_document = AsyncMock()
        app.running = True
        
        # Mock command handler registration
        command_handler = None
        def add_handler_mock(handler):
            nonlocal command_handler
            command_handler = handler
            # Get the command name from the handler's arguments
            command_name = next(iter(handler.commands))
            # Create a wrapper function that will be called by the test
            async def wrapper(update, context):
                wrapped_event = TelegramBotEvent(update, context)
                command = wrapped_event.get_command()
                metadata = wrapped_event.get_metadata()
                frame = CommandFrame(
                    command=command,
                    args=wrapped_event.get_command_args(),
                    metadata=metadata
                )
                # Get the transport's command handler
                transport = mock.get_transport()
                if transport and command in transport._command_handlers:
                    await transport._command_handlers[command](frame)
            # Create a simple async mock that stores the wrapper
            mock_callback = AsyncMock()
            mock_callback.__real_handler__ = wrapper
            command_handler.callback = mock_callback
        app.add_handler = Mock(side_effect=add_handler_mock)
        
        # Mock application builder
        builder = AsyncMock()
        builder.token = Mock(return_value=Mock(build=Mock(return_value=app)))
        mock.builder = Mock(return_value=builder)
        
        # Store command handler for testing
        mock.command_handler = lambda: command_handler
        # Store transport instance
        mock.set_transport = lambda t: setattr(mock, '_transport', t)
        mock.get_transport = lambda: getattr(mock, '_transport', None)
        yield mock

@pytest.mark.asyncio
async def test_user_transport_lifecycle(mock_telethon):
    """Test TelegramUserTransport start/stop lifecycle."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    # Test start
    await transport.start()
    mock_telethon.return_value.start.assert_awaited_once_with(phone="+1234567890")
    
    # Test stop
    await transport.stop()
    mock_telethon.return_value.disconnect.assert_awaited_once()

@pytest.mark.asyncio
async def test_bot_transport_lifecycle(mock_telegram_bot):
    """Test TelegramBotTransport start/stop lifecycle."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    app = mock_telegram_bot.builder().token().build()
    
    # Test start
    await transport.start()
    app.initialize.assert_awaited_once()
    app.start.assert_awaited_once()
    app.updater.start_polling.assert_awaited_once_with(
        drop_pending_updates=False,
        allowed_updates=['message']
    )
    
    # Test stop
    app.running = True
    await transport.stop()
    app.updater.stop.assert_awaited_once()
    app.stop.assert_awaited_once()

@pytest.mark.asyncio
async def test_user_transport_send_text(mock_telethon):
    """Test TelegramUserTransport sending text messages."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    frame = TextFrame(
        text="Hello, world!",
        metadata=EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1
        )
    )
    
    mock_telethon.return_value.send_message.return_value = Mock(id=1)
    result = await transport.send(frame)
    
    mock_telethon.return_value.send_message.assert_awaited_once_with(
        123456789,
        "Hello, world!"
    )
    assert result.metadata.message_id == 1

@pytest.mark.asyncio
async def test_bot_transport_send_text(mock_telegram_bot):
    """Test TelegramBotTransport sending text messages."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    app = mock_telegram_bot.builder().token().build()
    
    frame = TextFrame(
        text="Hello, world!",
        metadata=EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1
        )
    )
    
    app.bot.send_message.return_value = Mock(message_id=1)
    result = await transport.send(frame)
    
    app.bot.send_message.assert_awaited_once_with(
        chat_id=123456789,
        text="Hello, world!"
    )
    assert result.metadata.message_id == 1

@pytest.mark.asyncio
async def test_user_transport_send_image(mock_telethon):
    """Test TelegramUserTransport sending images."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    frame = ImageFrame(
        content=b"test_image_data",
        size=(100, 100),
        format="JPEG",
        metadata=EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1
        )
    )
    
    mock_telethon.return_value.send_file.return_value = Mock(id=1)
    result = await transport.send(frame)
    
    mock_telethon.return_value.send_file.assert_awaited_once_with(
        123456789,
        file=b"test_image_data",
        caption=None
    )
    assert result.metadata.message_id == 1

@pytest.mark.asyncio
async def test_bot_transport_send_image(mock_telegram_bot):
    """Test TelegramBotTransport sending images."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    app = mock_telegram_bot.builder().token().build()
    
    frame = ImageFrame(
        content=b"test_image_data",
        size=(100, 100),
        format="JPEG",
        metadata=EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1
        )
    )
    
    app.bot.send_photo.return_value = Mock(message_id=1)
    result = await transport.send(frame)
    
    app.bot.send_photo.assert_awaited_once_with(
        chat_id=123456789,
        photo=b"test_image_data",
        caption=None
    )
    assert result.metadata.message_id == 1

@pytest.mark.asyncio
async def test_user_transport_send_document(mock_telethon):
    """Test TelegramUserTransport sending documents."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    frame = DocumentFrame(
        content=b"test_document_data",
        filename="test.pdf",
        mime_type="application/pdf",
        caption="Test document",
        metadata=EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1
        )
    )
    
    mock_telethon.return_value.send_file.return_value = Mock(id=1)
    result = await transport.send(frame)
    
    mock_telethon.return_value.send_file.assert_awaited_once_with(
        123456789,
        file=b"test_document_data",
        caption="Test document",
        force_document=True
    )
    assert result.metadata.message_id == 1

@pytest.mark.asyncio
async def test_bot_transport_send_document(mock_telegram_bot):
    """Test TelegramBotTransport sending documents."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    app = mock_telegram_bot.builder().token().build()
    
    frame = DocumentFrame(
        content=b"test_document_data",
        filename="test.pdf",
        mime_type="application/pdf",
        caption="Test document",
        metadata=EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1
        )
    )
    
    app.bot.send_document.return_value = Mock(message_id=1)
    result = await transport.send(frame)
    
    app.bot.send_document.assert_awaited_once_with(
        chat_id=123456789,
        document=b"test_document_data",
        caption="Test document"
    )
    assert result.metadata.message_id == 1

@pytest.mark.asyncio
async def test_user_transport_error_handling(mock_telethon):
    """Test TelegramUserTransport error handling."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    frame = TextFrame(
        text="Hello, world!",
        metadata=EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1
        )
    )
    
    # Test network error
    mock_telethon.return_value.send_message.side_effect = ConnectionError("Network error")
    with pytest.raises(ConnectionError, match="Network error"):
        await transport.send(frame)
    
    # Test invalid chat error
    mock_telethon.return_value.send_message.side_effect = ValueError("Chat not found")
    with pytest.raises(ValueError, match="Chat not found"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_bot_transport_error_handling(mock_telegram_bot):
    """Test TelegramBotTransport error handling."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    app = mock_telegram_bot.builder().token().build()
    
    frame = TextFrame(
        text="Hello, world!",
        metadata=EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1
        )
    )
    
    # Test network error
    app.bot.send_message.side_effect = ConnectionError("Network error")
    with pytest.raises(ConnectionError, match="Network error"):
        await transport.send(frame)
    
    # Test invalid chat error
    app.bot.send_message.side_effect = ValueError("Chat not found")
    with pytest.raises(ValueError, match="Chat not found"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_user_transport_command_registration(mock_telethon):
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
    
    # Verify event handler was registered
    assert transport._event_handler is not None, "Command event handler not registered"
    
    # Mock an incoming command
    mock_event = AsyncMock()
    mock_event.message = AsyncMock()
    mock_event.message.text = "/test arg1 arg2"
    mock_event.message.id = 123
    mock_event.chat_id = 456
    mock_event.chat = AsyncMock()
    mock_event.chat.title = "Test Chat"
    mock_event.sender_id = 789
    mock_event.sender = AsyncMock()
    mock_event.sender.username = "testuser"
    
    # Get the real handler from the mock
    real_handler = transport._event_handler.__real_handler__
    
    # Trigger the event handler
    await real_handler(mock_event)
    
    # Verify handler was called with correct frame
    handler.assert_called_once()
    frame = handler.call_args[0][0]
    assert isinstance(frame, CommandFrame)
    assert frame.command == "/test"
    assert frame.args == ["arg1", "arg2"]
    assert frame.metadata.chat_id == 456
    assert frame.metadata.sender_id == 789

@pytest.mark.asyncio
async def test_bot_transport_command_registration(mock_telegram_bot):
    """Test command registration in TelegramBotTransport."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    app = mock_telegram_bot.builder().token().build()
    mock_telegram_bot.set_transport(transport)
    
    # Mock command handler
    handler = AsyncMock()
    await transport.register_command("test", handler)
    
    # Verify handler was registered
    assert "/test" in transport._command_handlers
    assert transport._command_handlers["/test"] == handler
    
    # Start transport to register command handler
    await transport.start()
    app.add_handler.assert_called_once()
    
    # Get the registered command handler
    command_handler = app.add_handler.call_args[0][0]
    assert isinstance(command_handler, CommandHandler)
    assert command_handler.commands == frozenset(["test"])
    
    # Mock an incoming command
    mock_update = AsyncMock()
    mock_update.message = AsyncMock()
    mock_update.message.text = "/test arg1 arg2"
    mock_update.message.message_id = 123
    mock_update.message.chat_id = 456
    mock_update.message.chat = AsyncMock()
    mock_update.message.chat.title = "Test Chat"
    mock_update.message.from_user = AsyncMock()
    mock_update.message.from_user.id = 789
    mock_update.message.from_user.username = "testuser"
    mock_update.message.from_user.first_name = "Test User"
    
    mock_context = AsyncMock()
    mock_context.args = ["arg1", "arg2"]
    
    # Get the real handler from the mock
    real_handler = command_handler.callback.__real_handler__
    
    # Trigger the command handler
    await real_handler(mock_update, mock_context)
    
    # Verify handler was called with correct frame
    handler.assert_called_once()
    frame = handler.call_args[0][0]
    assert isinstance(frame, CommandFrame)
    assert frame.command == "/test"
    assert frame.args == ["arg1", "arg2"]
    assert frame.metadata.chat_id == 456
    assert frame.metadata.chat_title == "Test Chat"
    assert frame.metadata.sender_id == 789
    assert frame.metadata.sender_name == "testuser"
    assert frame.metadata.message_id == 123

@pytest.mark.asyncio
async def test_user_transport_command_not_found(mock_telethon):
    """Test handling of unregistered commands in TelegramUserTransport."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )

    # Start transport to register event handler
    await transport.start()

    # Get the registered event handler
    assert hasattr(transport, '_event_handler'), "Event handler not stored"
    event_handler = transport._event_handler
    assert event_handler is not None, "Command event handler not registered"

    # Mock an incoming unregistered command
    mock_event = AsyncMock()
    mock_event.message = AsyncMock()
    mock_event.message.text = "/unknown"
    mock_event.message.id = 123
    mock_event.chat_id = 456
    mock_event.chat = AsyncMock()
    mock_event.chat.title = "Test Chat"
    mock_event.sender_id = 789
    mock_event.sender = AsyncMock()
    mock_event.sender.username = "testuser"

    # Get the real handler from the mock
    real_handler = event_handler.__real_handler__
    
    # Trigger the event handler - should not raise any errors
    await real_handler(mock_event) 