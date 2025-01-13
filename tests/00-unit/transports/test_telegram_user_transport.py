"""Unit tests for telegram user transport."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from telegram import Message, Chat, User, PhotoSize, File
from telethon import TelegramClient, events

from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.transports.telegram_transport import TelegramUserTransport

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_transport.TelegramClient')
async def test_user_transport_start_stop(mock_client):
    """Test starting and stopping the user transport."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"  # Use in-memory session for testing
    )
    
    # Mock the client
    mock_client.return_value.start = AsyncMock()
    mock_client.return_value.disconnect = AsyncMock()
    mock_client.return_value.get_me = AsyncMock(return_value=MagicMock(
        id=12345,
        first_name="Test User",
        username="testuser"
    ))
    mock_client.return_value.on = MagicMock()
    
    # Start transport
    await transport.start()
    
    # Verify start sequence
    mock_client.return_value.start.assert_awaited_once_with(phone="+1234567890")
    mock_client.return_value.get_me.assert_awaited_once()
    mock_client.return_value.on.assert_called_once_with(events.NewMessage)
    
    # Stop transport
    await transport.stop()
    
    # Verify stop sequence
    mock_client.return_value.disconnect.assert_awaited_once()

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_transport.TelegramClient')
async def test_user_transport_validates_params(mock_client):
    """Test that user transport validates its parameters."""
    # Test empty api_id
    with pytest.raises(ValueError, match="api_id must not be empty"):
        TelegramUserTransport(
            api_id="",
            api_hash="abc",
            phone_number="+1234567890",
            session_name=":memory:"
        )
    
    # Test empty api_hash
    with pytest.raises(ValueError, match="api_hash must not be empty"):
        TelegramUserTransport(
            api_id="123",
            api_hash="",
            phone_number="+1234567890",
            session_name=":memory:"
        )
    
    # Test empty phone_number
    with pytest.raises(ValueError, match="phone_number must not be empty"):
        TelegramUserTransport(
            api_id="123",
            api_hash="abc",
            phone_number="",
            session_name=":memory:"
        )
    
    # Test empty session_name
    with pytest.raises(ValueError, match="session_name must not be empty"):
        TelegramUserTransport(
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890",
            session_name=""
        )

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_transport.TelegramClient')
async def test_user_handle_command(mock_client):
    """Test handling of user commands."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )
    
    # Mock the message data
    message = MagicMock(spec=Message)
    message.text = "/start help"
    message.id = 12345
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
    
    # Track pushed frames
    pushed_frames = []
    transport.push_frame = AsyncMock(side_effect=lambda frame: pushed_frames.append(frame))
    
    # Handle command
    await transport._handle_command(message)
    
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

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_transport.TelegramClient')
async def test_user_send_photo_frame(mock_client):
    """Test sending photo frames through user transport."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )
    
    # Mock client
    mock_client.return_value.send_file = AsyncMock(return_value=MagicMock(id=12345))
    transport.client = mock_client.return_value
    
    # Create a test frame
    frame = ImageFrame(
        content=b"fake_photo_data",
        caption="Test caption",
        size=(800, 600),
        metadata={
            'chat_id': 67890,
            'thread_id': 22222,
            'mime_type': 'image/jpeg'
        }
    )
    
    # Send frame
    sent_frame = await transport.send(frame)
    
    # Verify client call
    mock_client.return_value.send_file.assert_awaited_once_with(
        chat_id=67890,
        file=b"fake_photo_data",
        caption="Test caption",
        reply_to=22222,
        force_document=False
    )
    
    # Verify sent frame
    assert sent_frame is frame
    assert sent_frame.metadata['message_id'] == 12345 