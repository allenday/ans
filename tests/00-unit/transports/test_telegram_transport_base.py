"""Unit tests for telegram transport base class."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from telegram import Bot, Update, Message, Chat, User, PhotoSize, File
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame, StickerFrame, AudioFrame, VoiceFrame
from chronicler.transports.base import BaseTransport
from chronicler.transports.telegram_transport import TelegramTransportBase

def test_transport_base_is_abstract():
    """Test that BaseTransport is abstract."""
    with pytest.raises(TypeError):
        BaseTransport()

def test_telegram_transport_base_is_abstract():
    """Test that TelegramTransportBase is abstract."""
    with pytest.raises(TypeError):
        TelegramTransportBase()

@pytest.mark.asyncio
async def test_base_push_frame():
    """Test that base push_frame method works."""
    class TestTransport(TelegramTransportBase):
        async def start(self): pass
        async def stop(self): pass
        async def send(self, frame): pass
    
    transport = TestTransport()
    frame = Frame(metadata={})
    
    # Mock the frame processor
    transport.frame_processor = AsyncMock()
    
    # Push frame
    await transport.push_frame(frame)
    
    # Verify frame was processed
    transport.frame_processor.process.assert_called_once_with(frame)

@pytest.mark.asyncio
async def test_base_handle_text_message():
    """Test handling of text messages with metadata."""
    class TestTransport(TelegramTransportBase):
        async def start(self): pass
        async def stop(self): pass
        async def send(self, frame): pass
    
    transport = TestTransport()
    
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
    message.chat = chat
    
    # Mock user data
    user = MagicMock(spec=User)
    user.id = 11111
    user.username = "testuser"
    message.from_user = user
    
    # Create update object
    update = MagicMock(spec=Update)
    update.message = message
    
    # Mock context
    context = AsyncMock()
    context.bot = AsyncMock()
    context.bot.get_file = AsyncMock()
    
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
    assert metadata['sender_id'] == 11111
    assert metadata['sender_name'] == "testuser"

@pytest.mark.asyncio
async def test_base_handle_command():
    """Test handling of commands."""
    class TestTransport(TelegramTransportBase):
        async def start(self): pass
        async def stop(self): pass
        async def send(self, frame): pass
    
    transport = TestTransport()
    
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
    
    # Verify metadata
    metadata = frame.metadata
    assert metadata['chat_id'] == 67890
    assert metadata['chat_title'] == "Test Chat"
    assert metadata['sender_id'] == 11111
    assert metadata['sender_name'] == "testuser"

@pytest.mark.asyncio
async def test_base_handle_photo():
    """Test handling of photo messages."""
    class TestTransport(TelegramTransportBase):
        async def start(self): pass
        async def stop(self): pass
        async def send(self, frame): pass
    
    transport = TestTransport()
    
    # Mock the message data
    message = MagicMock(spec=Message)
    message.caption = "Test photo"
    message.message_id = 12345
    message.date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    # Mock photo data
    photo = MagicMock(spec=PhotoSize)
    photo.file_id = "test_file_id"
    photo.width = 800
    photo.height = 600
    message.photo = [photo]  # List of photos, last one is highest quality
    
    # Mock file data
    file = MagicMock(spec=File)
    file.file_path = "photos/test.jpg"
    file.download_as_bytearray = AsyncMock(return_value=b"fake_photo_data")
    photo.get_file = AsyncMock(return_value=file)
    
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
    
    # Create update object
    update = MagicMock(spec=Update)
    update.message = message
    
    # Mock context
    context = MagicMock()
    context.bot.get_file = AsyncMock(return_value=file)
    
    # Track pushed frames
    pushed_frames = []
    transport.push_frame = AsyncMock(side_effect=lambda frame: pushed_frames.append(frame))
    
    # Handle message
    await transport._handle_message(update, context)
    
    # Verify frame was pushed
    assert len(pushed_frames) == 1
    frame = pushed_frames[0]
    
    # Verify frame type and content
    assert isinstance(frame, ImageFrame)
    assert frame.caption == "Test photo"
    assert frame.size == (800, 600)
    
    # Verify metadata
    metadata = frame.metadata
    assert metadata['chat_id'] == 67890
    assert metadata['chat_title'] == "Test Chat"
    assert metadata['sender_id'] == 11111
    assert metadata['sender_name'] == "testuser"
    assert metadata['mime_type'] == "image/jpeg"
    assert metadata['file_id'] == "test_file_id"

@pytest.mark.asyncio
async def test_base_handle_sticker():
    """Test handling of sticker messages."""
    class TestTransport(TelegramTransportBase):
        async def start(self): pass
        async def stop(self): pass
        async def send(self, frame): pass
    
    transport = TestTransport()
    
    # Mock the message data
    message = MagicMock(spec=Message)
    message.message_id = 12345
    message.date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    message.photo = None
    message.text = None
    
    # Mock sticker data
    sticker = MagicMock()
    sticker.file_id = "sticker123"
    sticker.width = 512
    sticker.height = 512
    sticker.emoji = "🎉"
    sticker.set_name = "TestStickerSet"
    sticker.is_animated = False
    sticker.is_video = False
    message.sticker = sticker
    
    # Mock file data
    file = MagicMock(spec=File)
    file.file_path = "stickers/test_sticker.webp"
    file.download_as_bytearray = AsyncMock(return_value=b"fake_sticker_data")
    
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
    
    # Create update object
    update = MagicMock(spec=Update)
    update.message = message
    
    # Mock context
    context = AsyncMock()
    context.bot = AsyncMock()
    context.bot.get_file = AsyncMock(return_value=file)
    
    # Track pushed frames
    pushed_frames = []
    transport.push_frame = AsyncMock(side_effect=lambda frame: pushed_frames.append(frame))
    
    # Handle message
    await transport._handle_message(update, context)
    
    # Verify frame was pushed
    assert len(pushed_frames) == 1
    frame = pushed_frames[0]
    
    # Verify frame type and content
    assert isinstance(frame, StickerFrame)
    assert frame.content == b"fake_sticker_data"
    assert frame.emoji == "🎉"
    assert frame.set_name == "TestStickerSet"
    
    # Verify metadata
    metadata = frame.metadata
    assert metadata['chat_id'] == 67890
    assert metadata['chat_title'] == "Test Chat"
    assert metadata['sender_id'] == 11111
    assert metadata['sender_name'] == "testuser"
    assert metadata['mime_type'] == "image/webp"
    assert metadata['file_id'] == "sticker123"
    assert metadata['is_animated'] == False
    assert metadata['is_video'] == False 