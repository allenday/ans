"""Mock implementations for Telegram transports."""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from telegram.ext import CommandHandler, Application
from telethon import events
from telegram.error import InvalidToken

from chronicler.frames import CommandFrame
from chronicler.transports.telegram_bot_event import TelegramBotEvent
from chronicler.transports.events import EventMetadata

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

@pytest.fixture
async def mock_telegram():
    """Mock telegram bot for testing.
    
    This fixture provides a comprehensive mock of the telegram bot,
    including application building and initialization.
    """
    # Create mock application
    app = AsyncMock()
    app.initialize = AsyncMock()
    app.start = AsyncMock()
    app.stop = AsyncMock()
    app.shutdown = AsyncMock()
    
    # Mock bot
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.get_me = AsyncMock()
    app.bot = bot
    
    # Store handlers
    handlers = []
    def add_handler_mock(handler):
        handlers.append(handler)
    app.add_handler = Mock(side_effect=add_handler_mock)
    app._handlers = handlers
    
    # Create a patched ApplicationBuilder that validates tokens
    class MockApplicationBuilder:
        def token(self, token):
            if not token:
                raise InvalidToken("Invalid token: You must pass the token you received from https://t.me/Botfather!")
            self._token = token
            return self
            
        def build(self):
            app.bot.token = self._token
            return app
    
    with patch('telegram.ext.ApplicationBuilder', return_value=MockApplicationBuilder()), \
         patch('telegram.ext.Application.initialize', new=app.initialize), \
         patch('telegram.ext.Application.start', new=app.start), \
         patch('telegram.ext.Application.stop', new=app.stop), \
         patch('telegram.Bot.get_me', new=app.bot.get_me):
        yield app 