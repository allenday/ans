"""Tests for telegram transport base class."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from chronicler.frames.command import CommandFrame
from chronicler.frames.media import ImageFrame, TextFrame
from chronicler.transports.telegram_transport import TelegramTransportBase
from chronicler.transports.telegram_bot_event import TelegramBotEvent
from chronicler.transports.telegram_bot_update import TelegramBotUpdate
from chronicler.transports.events import EventMetadata

class TestTransport(TelegramTransportBase):
    """Test transport implementation."""

    def __init__(self):
        """Initialize test transport."""
        super().__init__()
        self.frame_processor = AsyncMock()
        self._command_handlers = {}

    async def start(self):
        """Start the transport."""
        await super().start()

    async def stop(self):
        """Stop the transport."""
        await super().stop()

    async def send(self, frame):
        """Send a frame."""
        return frame

    async def process_frame(self, frame):
        """Process a frame."""
        if self.frame_processor:
            return await self.frame_processor(frame)
        return frame

    async def register_command(self, command, handler):
        """Register a command handler."""
        self._command_handlers[command] = handler

@pytest.mark.asyncio
async def test_transport_base_is_abstract():
    """Test that TelegramTransportBase is abstract."""
    with pytest.raises(TypeError):
        TelegramTransportBase()

@pytest.mark.asyncio
async def test_base_push_frame():
    """Test pushing frames through transport."""
    transport = TestTransport()
    transport.frame_processor = AsyncMock()
    transport.frame_processor.return_value = TextFrame(
        content="processed", 
        metadata=EventMetadata(chat_id=123)
    )

    frame = TextFrame(
        content="test", 
        metadata=EventMetadata(chat_id=123)
    )
    processed = await transport.process_frame(frame)

    transport.frame_processor.assert_called_once_with(frame)
    assert processed.content == "processed"

@pytest.mark.asyncio
async def test_base_handle_text_message():
    """Test handling text messages."""
    transport = TestTransport()
    transport.frame_processor = AsyncMock()
    transport.frame_processor.return_value = TextFrame(
        content="processed", 
        metadata=EventMetadata(chat_id=123)
    )

    # Create mock update
    mock_update = MagicMock()
    mock_update.message = MagicMock()
    mock_update.message.text = "test message"
    mock_update.message.chat = MagicMock()
    mock_update.message.chat.id = 123
    mock_update.message.chat.title = "Test Chat"
    mock_update.message.from_user = MagicMock()
    mock_update.message.from_user.id = 456
    mock_update.message.from_user.username = "Test User"
    mock_update.message.message_id = 789
    mock_update.message.date = MagicMock()
    mock_update.message.date.timestamp.return_value = 1234567890

    # Create TelegramBotUpdate wrapper
    update = TelegramBotUpdate(mock_update)

    # Create event with metadata
    event = TelegramBotEvent(update=update)

    frame = TextFrame(
        content=event.get_text(),
        metadata=event.get_metadata()
    )
    processed = await transport.process_frame(frame)

    transport.frame_processor.assert_called_once_with(frame)
    assert processed.content == "processed"

@pytest.mark.asyncio
async def test_base_handle_command():
    """Test handling commands."""
    transport = TestTransport()
    handler = AsyncMock()
    await transport.register_command("test", handler)

    # Create mock update
    mock_update = MagicMock()
    mock_update.message_text = "/test arg1 arg2"
    mock_update.chat_id = 123
    mock_update.chat_title = "Test Chat"
    mock_update.sender_id = 456
    mock_update.sender_name = "Test User"
    mock_update.message_id = 789
    mock_update.timestamp = 1234567890

    # Create TelegramBotUpdate wrapper
    update = TelegramBotUpdate(mock_update)

    # Create event
    event = TelegramBotEvent(update=update)

    assert "test" in transport._command_handlers
    assert transport._command_handlers["test"] == handler

@pytest.mark.asyncio
async def test_base_handle_photo():
    """Test handling photo messages."""
    transport = TestTransport()
    transport.frame_processor = AsyncMock()
    transport.frame_processor.return_value = ImageFrame(
        content=b"processed", 
        metadata=EventMetadata(chat_id=123)
    )

    # Create mock update with photo content
    mock_update = MagicMock()
    mock_update.message_text = None
    mock_update.photo_data = b"test_photo"
    mock_update.chat_id = 123
    mock_update.chat_title = "Test Chat"
    mock_update.sender_id = 456
    mock_update.sender_name = "Test User"
    mock_update.message_id = 789
    mock_update.timestamp = 1234567890

    # Create TelegramBotUpdate wrapper
    update = TelegramBotUpdate(mock_update)

    # Create event
    event = TelegramBotEvent(update=update)

    frame = ImageFrame(
        content=b"test_photo", 
        metadata=event.get_metadata()
    )
    processed = await transport.process_frame(frame)

    transport.frame_processor.assert_called_once_with(frame)
    assert processed.content == b"processed"

@pytest.mark.asyncio
async def test_base_handle_sticker():
    """Test handling sticker messages."""
    transport = TestTransport()
    transport.frame_processor = AsyncMock()
    transport.frame_processor.return_value = ImageFrame(
        content=b"processed", 
        metadata=EventMetadata(chat_id=123)
    )

    # Create mock update with sticker content
    mock_update = MagicMock()
    mock_update.message_text = None
    mock_update.sticker_data = b"test_sticker"
    mock_update.chat_id = 123
    mock_update.chat_title = "Test Chat"
    mock_update.sender_id = 456
    mock_update.sender_name = "Test User"
    mock_update.message_id = 789
    mock_update.timestamp = 1234567890

    # Create TelegramBotUpdate wrapper
    update = TelegramBotUpdate(mock_update)

    # Create event
    event = TelegramBotEvent(update=update)

    frame = ImageFrame(
        content=b"test_sticker", 
        metadata=event.get_metadata()
    )
    processed = await transport.process_frame(frame)

    transport.frame_processor.assert_called_once_with(frame)
    assert processed.content == b"processed" 