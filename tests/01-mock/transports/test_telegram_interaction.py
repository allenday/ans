"""Test interaction between Telegram transports."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from chronicler.frames.media import TextFrame
from chronicler.transports.telegram_factory import TelegramTransportFactory
from chronicler.transports.events import EventMetadata

@pytest.fixture
def mock_telethon():
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
                return handler
            return register_handler
        client.on = Mock(side_effect=on_mock)
        mock.return_value = client
        
        # Store event handler for testing
        mock.event_handler = lambda: event_handler
        yield mock

@pytest.fixture
def mock_python_telegram_bot():
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
        app.add_handler = Mock(side_effect=add_handler_mock)
        
        # Mock application builder
        builder = AsyncMock()
        builder.token = Mock(return_value=Mock(build=Mock(return_value=app)))
        mock.builder = Mock(return_value=builder)
        
        # Store command handler for testing
        mock.command_handler = lambda: command_handler
        yield mock

@pytest.mark.asyncio
async def test_user_to_bot_interaction(mock_telethon, mock_python_telegram_bot):
    """Test interaction between user and bot transports."""
    factory = TelegramTransportFactory()
    
    # Create user transport
    user_transport = factory.create_transport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    # Create bot transport
    bot_transport = factory.create_transport(bot_token="BOT:TOKEN")
    
    # Start both transports
    await user_transport.start()
    await bot_transport.start()
    
    try:
        # Create a test frame
        frame = TextFrame(
            text="Hello from user!",
            metadata=EventMetadata(
                chat_id=123456789,
                chat_title="Test Chat",
                sender_id=987654321,
                sender_name="Test User",
                message_id=None  # Will be set after sending
            )
        )
        
        # Setup mock responses
        mock_message = AsyncMock()
        mock_message.id = 1
        mock_telethon.return_value.send_message.return_value = mock_message
        
        bot_message = AsyncMock()
        bot_message.message_id = 2
        mock_python_telegram_bot.builder().token().build().bot.send_message.return_value = bot_message
        
        # User sends message
        sent_frame = await user_transport.send(frame)
        assert sent_frame.metadata.message_id == 1
        mock_telethon.return_value.send_message.assert_awaited_once_with(
            123456789,
            "Hello from user!"
        )
        
        # Bot processes and responds
        response_frame = TextFrame(
            text="Hello from bot!",
            metadata=EventMetadata(
                chat_id=123456789,
                chat_title="Test Chat",
                sender_id=111111111,
                sender_name="Test Bot",
                message_id=None  # Will be set after sending
            )
        )
        sent_response = await bot_transport.send(response_frame)
        assert sent_response.metadata.message_id == 2
        mock_python_telegram_bot.builder().token().build().bot.send_message.assert_awaited_once_with(
            chat_id=123456789,
            text="Hello from bot!"
        )
    finally:
        # Stop both transports
        await user_transport.stop()
        await bot_transport.stop()

@pytest.mark.asyncio
async def test_transport_error_propagation(mock_telethon, mock_python_telegram_bot):
    """Test error handling and propagation in transports."""
    factory = TelegramTransportFactory()
    
    # Create transports
    user_transport = factory.create_transport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    bot_transport = factory.create_transport(bot_token="BOT:TOKEN")
    
    # Start transports
    await user_transport.start()
    await bot_transport.start()
    
    try:
        # Create test frame
        frame = TextFrame(
            text="Test message",
            metadata=EventMetadata(
                chat_id=123456789,
                chat_title="Test Chat",
                sender_id=987654321,
                sender_name="Test User",
                message_id=None  # Will be set after sending
            )
        )
        
        # Setup mock errors
        mock_telethon.return_value.send_message.side_effect = Exception("Telethon error")
        mock_python_telegram_bot.builder().token().build().bot.send_message.side_effect = Exception("Bot error")
        
        # Test user transport error
        with pytest.raises(Exception, match="Telethon error"):
            await user_transport.send(frame)
        
        # Test bot transport error
        with pytest.raises(Exception, match="Bot error"):
            await bot_transport.send(frame)
    finally:
        await user_transport.stop()
        await bot_transport.stop()

@pytest.mark.asyncio
async def test_transport_metadata_validation(mock_telethon, mock_python_telegram_bot):
    """Test metadata validation in transports."""
    factory = TelegramTransportFactory()
    
    # Create transports
    user_transport = factory.create_transport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    bot_transport = factory.create_transport(bot_token="BOT:TOKEN")
    
    # Start transports
    await user_transport.start()
    await bot_transport.start()
    
    try:
        # Create frame without metadata
        frame = TextFrame(text="Test message")
        
        # Test user transport validation
        with pytest.raises(ValueError, match="Frame must have EventMetadata"):
            await user_transport.send(frame)
        
        # Test bot transport validation
        with pytest.raises(ValueError, match="Frame must have EventMetadata"):
            await bot_transport.send(frame)
        
        # Create frame with invalid metadata type
        frame = TextFrame(
            text="Test message",
            metadata={"chat_id": 123}  # Not an EventMetadata instance
        )
        
        # Test user transport validation
        with pytest.raises(ValueError, match="Frame must have EventMetadata"):
            await user_transport.send(frame)
        
        # Test bot transport validation
        with pytest.raises(ValueError, match="Frame must have EventMetadata"):
            await bot_transport.send(frame)
    finally:
        await user_transport.stop()
        await bot_transport.stop()

@pytest.mark.asyncio
async def test_transport_lifecycle(mock_telethon, mock_python_telegram_bot):
    """Test transport lifecycle management."""
    factory = TelegramTransportFactory()
    
    # Create transports
    user_transport = factory.create_transport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    bot_transport = factory.create_transport(bot_token="BOT:TOKEN")
    
    # Test user transport lifecycle
    await user_transport.start()
    mock_telethon.return_value.start.assert_awaited_once()
    await user_transport.stop()
    mock_telethon.return_value.disconnect.assert_awaited_once()
    
    # Test bot transport lifecycle
    await bot_transport.start()
    mock_python_telegram_bot.builder().token().build().initialize.assert_awaited_once()
    mock_python_telegram_bot.builder().token().build().start.assert_awaited_once()
    await bot_transport.stop()
    mock_python_telegram_bot.builder().token().build().updater.stop.assert_awaited_once()
    mock_python_telegram_bot.builder().token().build().stop.assert_awaited_once() 