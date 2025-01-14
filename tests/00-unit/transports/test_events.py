"""Unit tests for event abstractions."""
import pytest
from unittest.mock import Mock
from datetime import datetime

from chronicler.transports.events import (
    EventMetadata,
    TelethonEvent,
    TelegramBotEvent
)

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

def test_telethon_event():
    """Test TelethonEvent wrapper."""
    # Mock Telethon event
    mock_event = Mock()
    mock_event.message = Mock(text="/test arg1 arg2", id=123)
    mock_event.chat_id = 456
    mock_event.chat = Mock(title="Test Chat")
    mock_event.sender_id = 789
    mock_event.sender = Mock(username="testuser", first_name="Test User")
    
    event = TelethonEvent(mock_event)
    
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
    
    event = TelethonEvent(mock_event)
    metadata = event.get_metadata()
    
    assert metadata.sender_id is None
    assert metadata.sender_name is None
    assert metadata.chat_title is None

def test_telegram_bot_event():
    """Test TelegramBotEvent wrapper."""
    # Mock python-telegram-bot update and context
    mock_update = Mock()
    mock_update.message = Mock(
        text="/test arg1 arg2",
        message_id=123,
        chat_id=456,
        chat=Mock(title="Test Chat")
    )
    mock_update.message.from_user = Mock(
        id=789,
        username="testuser",
        first_name="Test User"
    )
    
    mock_context = Mock(args=["arg1", "arg2"])
    
    event = TelegramBotEvent(mock_update, mock_context)
    
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

def test_telegram_bot_event_missing_sender():
    """Test TelegramBotEvent with missing sender info."""
    # Mock update with missing sender
    mock_update = Mock()
    mock_update.message = Mock(
        text="/test",
        message_id=123,
        chat_id=456,
        chat=Mock(title=None),
        from_user=None
    )
    mock_context = Mock(args=[])
    
    event = TelegramBotEvent(mock_update, mock_context)
    metadata = event.get_metadata()
    
    assert metadata.sender_id is None
    assert metadata.sender_name is None
    assert metadata.chat_title is None

def test_telegram_bot_event_fallback_args():
    """Test TelegramBotEvent falls back to text parsing when context.args is None."""
    mock_update = Mock()
    mock_update.message = Mock(
        text="/test arg1 arg2",
        message_id=123,
        chat_id=456,
        chat=Mock(title="Test Chat"),
        from_user=Mock(id=789, username="testuser")
    )
    mock_context = Mock(args=None)
    
    event = TelegramBotEvent(mock_update, mock_context)
    assert event.get_command_args() == ["arg1", "arg2"] 