"""Unit tests for telegram bot transport."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from telegram import Bot, Update, Message, Chat, User, PhotoSize, File
from telegram.ext import Application

from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.transports.telegram_transport import TelegramBotTransport

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_transport.Application')
async def test_bot_transport_start_stop(mock_app):
    """Test starting and stopping the bot transport."""
    transport = TelegramBotTransport(token="test:token")
    
    # Create an AsyncMock instance for the application
    app_instance = AsyncMock()
    app_instance.initialize = AsyncMock()
    app_instance.start = AsyncMock()
    app_instance.stop = AsyncMock()
    app_instance.updater.start_polling = AsyncMock()
    app_instance.updater.stop = AsyncMock()
    app_instance.bot.get_me = AsyncMock(return_value=AsyncMock(
        id=12345,
        first_name="Test Bot",
        username="testbot"
    ))
    app_instance.running = True
    
    # Mock the application builder
    mock_app.builder.return_value.token.return_value.build.return_value = app_instance
    transport.app = app_instance  # Set the app instance directly
    
    # Start transport
    await transport.start()
    
    # Verify start sequence
    app_instance.initialize.assert_awaited_once()
    app_instance.start.assert_awaited_once()
    app_instance.updater.start_polling.assert_awaited_once_with(drop_pending_updates=False, allowed_updates=['message'])
    
    # Stop transport
    await transport.stop()
    
    # Verify stop sequence
    app_instance.updater.stop.assert_awaited_once()
    app_instance.stop.assert_awaited_once()

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_transport.Application')
async def test_bot_transport_start_error(mock_app):
    """Test error handling during bot transport start."""
    transport = TelegramBotTransport(token="test:token")
    
    # Create an AsyncMock instance for the application
    app_instance = AsyncMock()
    app_instance.initialize = AsyncMock(side_effect=Exception("Test error"))
    
    # Mock the application builder
    mock_app.builder.return_value.token.return_value.build.return_value = app_instance
    transport.app = app_instance  # Set the app instance directly
    
    # Start should raise the error
    with pytest.raises(Exception, match="Test error"):
        await transport.start()

@pytest.mark.asyncio
async def test_bot_handle_text_message():
    """Test handling of text messages with various metadata."""
    transport = TelegramBotTransport(token="test:token")
    
    # Mock the message data
    message = MagicMock(spec=Message)
    message.text = "Test message"
    message.message_id = 12345
    message.date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    message.photo = None
    message.sticker = None
    
    # Mock chat data
    chat = MagicMock(spec=Chat)
    chat.id = 67890
    chat.title = "Test Chat"
    chat.type = "supergroup"
    chat.is_forum = True
    message.chat = chat
    
    # Mock user data
    user = MagicMock(spec=User)
    user.id = 11111
    user.username = "testuser"
    user.first_name = "Test"
    message.from_user = user
    
    # Mock thread data
    message.message_thread_id = 22222
    forum_topic = MagicMock()
    forum_topic.name = "Test Topic"
    message.forum_topic_created = forum_topic
    
    # Create update object
    update = MagicMock(spec=Update)
    update.message = message
    
    # Mock context
    context = MagicMock()
    
    # Track pushed frames
    pushed_frames = []
    transport.push_frame = AsyncMock(side_effect=lambda frame: pushed_frames.append(frame))
    
    # Handle message
    await transport._handle_message(update, context)
    
    # Verify frame was pushed
    assert len(pushed_frames) == 1
    frame = pushed_frames[0]
    
    # Verify frame type and content
    assert isinstance(frame, TextFrame)
    assert frame.content == "Test message"
    
    # Verify metadata
    metadata = frame.metadata
    assert metadata['chat_id'] == 67890
    assert metadata['chat_title'] == "Test Chat"
    assert metadata['thread_id'] == 22222
    assert metadata['thread_name'] == "Test Topic"
    assert metadata['sender_id'] == 11111
    assert metadata['sender_name'] == "testuser"

@pytest.mark.asyncio
async def test_bot_handle_command():
    """Test handling of bot commands."""
    transport = TelegramBotTransport(token="test:token")
    
    # Mock the message data
    message = MagicMock(spec=Message)
    message.text = "/start help"
    message.message_id = 12345
    message.date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    # Mock chat data
    chat = MagicMock(spec=Chat)
    chat.id = 67890
    chat.title = "Test Chat"
    chat.type = "supergroup"
    message.chat = chat
    
    # Mock user data
    user = MagicMock(spec=User)
    user.id = 11111
    user.username = "testuser"
    message.from_user = user
    
    # Mock entities data
    entity = MagicMock()
    entity.type = "bot_command"
    entity.offset = 0
    entity.length = 6  # Length of "/start"
    message.entities = [entity]
    
    # Create update object
    update = MagicMock(spec=Update)
    update.message = message
    
    # Mock context
    context = MagicMock()
    
    # Track pushed frames
    pushed_frames = []
    transport.push_frame = AsyncMock(side_effect=lambda frame: pushed_frames.append(frame))
    
    # Handle command
    await transport._handle_command(update, context)
    
    # Verify frame was pushed
    assert len(pushed_frames) == 1
    frame = pushed_frames[0]
    
    # Verify frame type and content
    assert isinstance(frame, CommandFrame)
    assert frame.command == "/start"
    assert frame.args == ["help"]
    assert frame.metadata == {
        'chat_id': 67890,
        'chat_title': "Test Chat",
        'sender_id': 11111,
        'sender_name': "testuser"
    } 