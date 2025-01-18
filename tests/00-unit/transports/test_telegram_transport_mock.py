"""Mock tests for Telegram transports."""
import pytest
from unittest.mock import Mock, patch

from chronicler.frames import TextFrame, ImageFrame, DocumentFrame, CommandFrame
from chronicler.transports.telegram_factory import (
    TelegramUserTransport,
    TelegramBotTransport
)
from chronicler.transports.events import TelegramBotEvent, EventMetadata
from tests.mocks.transports import create_mock_telethon, create_mock_telegram_bot

@pytest.fixture
def mock_telethon():
    """Mock Telethon client."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock:
        client = create_mock_telethon()
        mock.return_value = client
        yield mock

@pytest.fixture
def mock_telegram_bot():
    """Mock python-telegram-bot Application."""
    with patch('chronicler.transports.telegram_factory.Application') as mock:
        app = create_mock_telegram_bot()
        
        # Mock application builder
        builder = Mock()
        builder.token = Mock(return_value=Mock(build=Mock(return_value=app)))
        mock.builder = Mock(return_value=builder)
        
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