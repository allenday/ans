"""Test interaction between Telegram transports."""
import pytest
from unittest.mock import Mock, patch

from chronicler.frames.media import TextFrame
from chronicler.transports.telegram_factory import TelegramTransportFactory
from chronicler.transports.events import EventMetadata
from tests.mocks.transports import create_mock_telethon, create_mock_telegram_bot

@pytest.fixture
def mock_telethon():
    """Mock Telethon client."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock:
        client = create_mock_telethon()
        mock.return_value = client
        yield mock

@pytest.fixture
def mock_python_telegram_bot():
    """Mock python-telegram-bot Application."""
    with patch('chronicler.transports.telegram_factory.Application') as mock:
        app = create_mock_telegram_bot()
        
        # Mock application builder
        builder = Mock()
        builder.token = Mock(return_value=Mock(build=Mock(return_value=app)))
        mock.builder = Mock(return_value=builder)
        
        yield mock

@pytest.mark.asyncio
async def test_user_to_bot_interaction(mock_telethon, mock_python_telegram_bot):
    """Test interaction between user and bot transports."""
    # Create transports
    factory = TelegramTransportFactory()
    user_transport = factory.create_transport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    bot_transport = factory.create_transport(
        bot_token="BOT:TOKEN"
    )
    
    try:
        # Start both transports
        await user_transport.start()
        await bot_transport.start()
        
        # User sends message
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