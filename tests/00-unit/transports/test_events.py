"""Unit tests for event abstractions."""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from chronicler.transports.events import EventMetadata, Update
from chronicler.transports.telegram_bot_event import TelegramBotEvent

def test_event_metadata():
    """Test EventMetadata creation and defaults."""
    # Test required fields
    metadata = EventMetadata(
        chat_id=123,
        chat_title="Test Chat",
        sender_id=456,
        sender_name="Test User",
        message_id=789
    )
    assert metadata.chat_id == 123
    assert metadata.chat_title == "Test Chat"
    assert metadata.sender_id == 456
    assert metadata.sender_name == "Test User"
    assert metadata.message_id == 789
    
    # Test defaults for future platform fields
    assert metadata.platform == "telegram"
    assert metadata.timestamp is None
    assert metadata.reply_to is None
    assert metadata.thread_id is None
    assert metadata.channel_id is None
    assert metadata.guild_id is None
    assert metadata.is_private is False
    assert metadata.is_group is False

def test_update():
    """Test TelethonEvent wrapper."""
    # Mock Telethon event
    mock_event = Mock()
    mock_event.message = Mock(text="/test arg1 arg2", id=123)
    mock_event.chat_id = 456
    mock_event.chat = Mock(title="Test Chat")
    mock_event.sender_id = 789
    mock_event.sender = Mock(username="testuser", first_name="Test User")
    
    event = Update(mock_event)
    
    # Test text extraction
    assert event.get_text() == "/test arg1 arg2"
    
    # Test metadata extraction
    metadata = event.get_metadata()
    assert metadata.chat_id == 456
    assert metadata.chat_title == "Test Chat"
    assert metadata.sender_id == 789
    assert metadata.sender_name == "testuser"
    assert metadata.message_id == 123
    
    # Test command parsing
    assert event.get_command() == "/test"
    assert event.get_command_args() == ["arg1", "arg2"]

def test_telethon_event_missing_sender():
    """Test TelethonEvent with missing sender info."""
    # Mock Telethon event with missing sender
    mock_event = Mock()
    mock_event.message = Mock(text="/test", id=123)
    mock_event.chat_id = 456
    mock_event.chat = Mock(title=None)
    mock_event.sender_id = None
    mock_event.sender = None
    
    event = Update(mock_event)
    metadata = event.get_metadata()
    
    assert metadata.sender_id is None
    assert metadata.sender_name is None
    assert metadata.chat_title is None

def test_telegram_bot_event():
    """Test TelegramBotEvent."""
    # Create mock update with all fields
    mock_message = Mock()
    mock_message.text = "test message"
    mock_message.chat.id = 123
    mock_message.chat.title = "Test Chat"
    mock_message.from_user.id = 456
    mock_message.from_user.first_name = "Test User"
    mock_message.message_id = 789
    mock_message.date = datetime.fromtimestamp(1234567890)

    mock_update = Mock()
    mock_update.message = mock_message
    mock_update.chat_id = 123
    mock_update.chat_title = "Test Chat"
    mock_update.sender_id = 456
    mock_update.sender_name = "Test User"
    mock_update.message_id = 789
    mock_update.timestamp = 1234567890.0
    mock_update.message_text = "test message"

    event = TelegramBotEvent(mock_update)

    assert event.get_text() == "test message"
    metadata = event.get_metadata()
    assert metadata.chat_id == 123
    assert metadata.chat_title == "Test Chat"
    assert metadata.sender_id == 456
    assert metadata.sender_name == "Test User"
    assert metadata.message_id == 789
    assert metadata.timestamp == 1234567890.0

def test_telegram_bot_event_missing_sender():
    """Test TelegramBotEvent with missing sender info."""
    # Create mock update with minimal fields
    mock_message = Mock()
    mock_message.text = "test message"
    mock_message.chat.id = 123
    mock_message.chat.title = None
    mock_message.from_user = None
    mock_message.message_id = 789
    mock_message.date = datetime.fromtimestamp(1234567890)
    mock_message.message_thread_id = None

    mock_update = Mock()
    mock_update.message = mock_message
    mock_update.chat_id = 123
    mock_update.chat_title = None
    mock_update.sender_id = None
    mock_update.sender_name = None
    mock_update.message_id = 789
    mock_update.thread_id = None
    mock_update.timestamp = 1234567890.0
    mock_update.message_text = "test message"

    event = TelegramBotEvent(mock_update)

    assert event.get_text() == "test message"
    metadata = event.get_metadata()
    assert metadata.chat_id == 123
    assert metadata.chat_title is None
    assert metadata.sender_id is None
    assert metadata.sender_name is None
    assert metadata.message_id == 789
    assert metadata.timestamp == 1234567890.0

def test_telegram_bot_event_fallback_args():
    """Test TelegramBotEvent with fallback args."""
    # Create mock update with minimal fields
    mock_message = MagicMock()
    mock_message.text = "test message"
    mock_message.chat.id = 123
    mock_message.chat.title = None  # Test fallback
    mock_message.from_user = None  # Test fallback
    mock_message.message_id = 789
    mock_message.date = datetime.fromtimestamp(1234567890)
    
    mock_update = MagicMock()
    mock_update.message = mock_message

    # Create event with metadata
    metadata = EventMetadata(
        chat_id=123,
        chat_title="Fallback Chat",
        sender_id=456,
        sender_name="Fallback User",
        message_id=789
    )
    event = TelegramBotEvent(mock_update, metadata=metadata)

    # Verify metadata is preserved
    assert event.get_metadata().chat_id == 123
    assert event.get_metadata().chat_title == "Fallback Chat"
    assert event.get_metadata().sender_id == 456
    assert event.get_metadata().sender_name == "Fallback User"
    assert event.get_metadata().message_id == 789 