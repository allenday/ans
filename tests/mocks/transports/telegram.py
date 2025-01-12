"""Mock implementations for Telegram transports."""
import asyncio
from unittest.mock import AsyncMock, Mock
from telegram.ext import CommandHandler, Application
from telethon import events

from chronicler.frames import CommandFrame
from chronicler.transports.events import TelegramBotEvent, EventMetadata

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

def create_mock_telegram_bot():
    """Create a mock python-telegram-bot Application."""
    app = AsyncMock()
    
    # Mock basic app operations
    app.initialize = AsyncMock()
    app.start = AsyncMock()
    app.stop = AsyncMock()
    app.running = True
    
    # Mock bot instance
    app.bot = AsyncMock()
    app.bot.get_me = AsyncMock(return_value=Mock(
        id=12345,
        username="test_bot",
        first_name="Test Bot",
        is_bot=True
    ))
    app.bot.send_message = AsyncMock()
    app.bot.send_photo = AsyncMock()
    app.bot.send_document = AsyncMock()
    
    # Mock updater
    app.updater = AsyncMock()
    app.updater.start_polling = AsyncMock()
    app.updater.stop = AsyncMock()
    
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
            transport = app._transport
            if transport and command in transport._command_handlers:
                await transport._command_handlers[command](frame)
        # Create a simple async mock that stores the wrapper
        mock_callback = AsyncMock()
        mock_callback.__real_handler__ = wrapper
        command_handler.callback = mock_callback
    app.add_handler = Mock(side_effect=add_handler_mock)
    app.remove_handler = Mock()
    
    # Store command handler and transport for testing
    app._command_handler = command_handler
    app._transport = None
    
    return app 