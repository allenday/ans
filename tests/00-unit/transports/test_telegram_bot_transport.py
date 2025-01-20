"""Tests for telegram bot transport."""
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from telegram.error import InvalidToken, NetworkError, TelegramError
from telegram import Message, Chat, User, Update, PhotoSize, File, Bot
from telegram.ext import CallbackContext, MessageHandler, filters, CommandHandler, Application
import json

from chronicler.logging import get_logger, trace_operation
from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.frames.command import CommandFrame
from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from chronicler.transports.base import TransportError
from chronicler.transports.telegram_bot_event import TelegramBotEvent
from chronicler.transports.events import EventMetadata, Update
from chronicler.transports.telegram_bot_update import TelegramBotUpdate
from tests.mocks.transports.telegram import mock_telegram_complete, mock_telegram_app, mock_telegram_init

logger = get_logger(__name__, component="test.transport.telegram_bot")

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.initialization")
async def test_bot_initialization(mock_telegram_init):
    """Test bot initialization with mocked request."""
    logger.info("Testing bot initialization")
    
    transport = TelegramBotTransport("test_token")
    await transport.start()
    assert transport.is_running

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.lifecycle")
async def test_bot_transport_lifecycle(mock_telegram_init):
    """Test bot transport lifecycle."""
    logger.info("Bot transport lifecycle test started")

    transport = TelegramBotTransport("test_token")
    await transport.start()

    assert transport._initialized is True
    await transport.stop()
    assert not transport.is_running

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.send_text")
async def test_bot_transport_send_text(mock_telegram_init):
    """Test sending text message."""
    logger.info("Bot transport send text test started")

    transport = TelegramBotTransport("test_token")
    await transport.start()

    frame = TextFrame("test message")
    await transport.send(frame)

    # Verify bot.send_message was called
    mock_telegram_init.bot.send_message.assert_called_once_with(
        chat_id=frame.chat_id,
        text=frame.text
    )

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.send_photo")
async def test_bot_transport_send_photo(mock_telegram_init):
    """Test sending photo."""
    logger.info("Bot transport send photo test started")

    transport = TelegramBotTransport("test_token")
    await transport.start()

    frame = ImageFrame(content=b"test_photo_data", caption="test caption")
    await transport.send(frame)

    # Verify bot.send_photo was called
    mock_telegram_init.bot.send_photo.assert_called_once_with(
        chat_id=frame.chat_id,
        photo=frame.content,
        caption=frame.caption
    )

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.send_unsupported")
async def test_bot_transport_send_unsupported_frame(mock_telegram_init):
    """Test bot transport send unsupported frame."""
    logger.info("Testing bot transport send unsupported frame")
    
    transport = TelegramBotTransport("test_token")
    await transport.start()
    
    frame = Frame()
    frame.metadata["chat_id"] = 123456
    logger.debug(f"Attempting to send unsupported frame: {frame}")
    with pytest.raises(TransportError, match="Unsupported frame type"):
        await transport.send(frame)
    logger.info("Bot transport send unsupported frame test completed")

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.send_error")
async def test_bot_transport_send_error(mock_telegram_init):
    """Test bot transport send error."""
    logger.info("Testing bot transport send error")
    
    transport = TelegramBotTransport("test_token")
    await transport.start()
    
    # Override the mock to raise an error
    logger.debug("Setting up mock to raise NetworkError")
    mock_telegram_init.bot.send_message.side_effect = NetworkError("Failed to send message")
    
    frame = TextFrame(content="test message")
    frame.metadata["chat_id"] = 123456
    logger.debug(f"Attempting to send frame that should fail: {frame}")
    
    with pytest.raises(TransportError, match="Failed to send message"):
        await transport.send(frame)
    logger.info("Bot transport send error test completed")

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.handle_text")
async def test_bot_transport_handle_text(mock_telegram_init):
    """Test handling text message."""
    logger.info("Bot transport handle text test started")

    transport = TelegramBotTransport("test_token")
    await transport.start()

    # Create mock update
    mock_message = AsyncMock()
    mock_message.text = "test message"
    mock_message.chat.id = 123
    mock_update = AsyncMock()
    mock_update.message = mock_message

    # Register message handler
    handler_called = False
    async def message_handler(frame):
        nonlocal handler_called
        handler_called = True
        assert isinstance(frame, TextFrame)
        assert frame.text == "test message"
        assert frame.chat_id == 123

    transport.register_message_handler(message_handler)

    # Simulate message
    await transport._handle_message(TelegramBotUpdate(mock_update), None)
    assert handler_called

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.command_handling")
async def test_bot_transport_command_handling(mock_telegram_init):
    """Test handling command messages."""
    logger.info("Testing bot transport command handling")
    
    transport = TelegramBotTransport("test_token")
    await transport.start()
    
    # Register command handler
    command_called = False
    async def test_handler(event):
        nonlocal command_called
        logger.debug("Command handler called")
        command_called = True
    
    logger.debug("Registering command handler")
    await transport.register_command("test", test_handler)
    
    # Create mock update
    logger.debug("Creating mock command update")
    mock_message = Message(
        message_id=789,
        date=datetime.now(timezone.utc),
        chat=Chat(id=123456, type="private"),
        from_user=User(id=123456, first_name="Test User", username="testuser", is_bot=False),
        text="/test arg1 arg2"
    )
    mock_update = Update(1)
    mock_update.message = mock_message
    
    # Call handler
    logger.debug("Calling command handler")
    await transport._handle_command(TelegramBotUpdate(mock_update), None, test_handler)
    
    assert command_called, "Command handler should have been called"
    logger.info("Bot transport command handling test completed")

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.stop")
async def test_bot_transport_stop(mock_telegram_init):
    """Test bot transport stop."""
    logger.info("Testing bot transport stop")
    
    transport = TelegramBotTransport("test_token")
    await transport.start()
    
    logger.debug("Transport started, now stopping")
    await transport.stop()
    
    assert mock_telegram_init.bot.stop.called, "Bot stop should be called"
    assert mock_telegram_init.stop.called, "App stop should be called"
    assert mock_telegram_init.shutdown.called, "App shutdown should be called"
    logger.info("Bot transport stop test completed")

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.send_errors")
async def test_bot_transport_send_errors(mock_telegram_init):
    """Test sending errors."""
    logger.info("Bot transport send errors test started")

    transport = TelegramBotTransport("test_token")
    await transport.start()

    # Test network error
    mock_telegram_init.bot.send_message.side_effect = NetworkError("Network error")
    with pytest.raises(TransportError, match="Failed to send message: Network error"):
        await transport.send(TextFrame("test message"))

    # Test other error
    mock_telegram_init.bot.send_message.side_effect = TelegramError("Other error")
    with pytest.raises(TransportError, match="Failed to send message: Other error"):
        await transport.send(TextFrame("test message"))

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.empty_token")
async def test_bot_transport_empty_token():
    """Test that empty token raises TransportError."""
    logger.info("Bot transport empty token test started")
    with pytest.raises(TransportError, match="Invalid token: You must pass the token you received from https://t.me/Botfather!"):
        TelegramBotTransport("")

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.invalid_token")
async def test_bot_transport_invalid_token(mock_telegram_init):
    """Test invalid token."""
    logger.info("Bot transport invalid token test started")

    # Make initialize raise InvalidToken
    mock_telegram_init.initialize.side_effect = InvalidToken("The token `invalid_token` was rejected by the server.")

    transport = TelegramBotTransport("invalid_token")
    with pytest.raises(TransportError, match="Invalid token: The token `invalid_token` was rejected by the server."):
        await transport.start()

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_bot.valid_token")
async def test_bot_transport_valid_token(mock_telegram_init):
    """Test valid token."""
    logger.info("Bot transport valid token test started")

    transport = TelegramBotTransport("test_token")
    await transport.start()

    assert transport._initialized is True
    await transport.stop()
    assert not transport.is_running
    
    logger.info("Bot transport valid token test completed")