import pytest
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
from chronicler.transports.telegram_bot_transport import TelegramBotTransport, TelegramBotEvent

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