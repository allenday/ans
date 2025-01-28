"""Mock implementations for Telethon client."""
import pytest
import pytest_asyncio
import os
from unittest.mock import AsyncMock, Mock, call, MagicMock, patch
from telegram.ext import ApplicationBuilder, CommandHandler, ExtBot, Application
from telegram.error import InvalidToken
from typing import Optional, Tuple, Dict
from telegram.request import RequestData, BaseRequest
import json
from telegram import Bot
import asyncio

from chronicler.exceptions import TransportError
from chronicler.frames import CommandFrame
from chronicler.transports.events import EventMetadata
from chronicler.transports.telegram.transport.bot import TelegramBotTransport
from chronicler.transports.telegram_bot_event import TelegramBotEvent
from chronicler.transports.telegram.transport.user import TelegramUserTransport

from telethon import events

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

@pytest_asyncio.fixture
async def mock_session_path(tmp_path):
    """Mock session path for testing."""
    return tmp_path / "test_session"

@pytest.fixture
def mock_telethon(mock_session_path):
    """Create a mock Telethon client."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock:
        client = create_mock_telethon()
        
        # Mock session with custom path
        client.session = MagicMock()
        client.session.save = MagicMock()
        client.session.session_file = os.path.join(mock_session_path, "test_session.session")
        
        mock.return_value = client
        yield mock

@pytest_asyncio.fixture
async def mock_telegram_user_client():
    """Create a mock Telethon client for testing."""
    return create_mock_telethon()

@pytest_asyncio.fixture
async def user_transport(mock_telegram_user_client, monkeypatch):
    """Create a user transport instance."""
    # Patch TelegramClient to return our mock
    monkeypatch.setattr('chronicler.transports.telegram.transport.user.TelegramClient', Mock(return_value=mock_telegram_user_client))
    
    transport = TelegramUserTransport(
        api_id=123456789,
        api_hash="test_hash",
        phone_number="+1234567890"
    )
    transport._client = mock_telegram_user_client
    transport._initialized = True  # Since we're mocking, we can set this directly
    
    # Set up message sender
    mock_sender = AsyncMock()
    mock_sender.send = AsyncMock()
    transport._message_sender = mock_sender
    
    return transport