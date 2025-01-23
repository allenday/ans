"""Tests for telegram interaction."""
import pytest
import pytest_asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch
from telegram import Bot, Message, Chat, User, Update, PhotoSize
from telegram.ext import ApplicationBuilder
from chronicler.frames import TextFrame
from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from chronicler.transports.telegram_user_transport import TelegramUserTransport
from chronicler.logging.config import trace_operation
from tests.mocks.transports.telethon import create_mock_telethon
from tests.mocks.transports.telegram import mock_telegram_bot

logger = logging.getLogger(__name__)

@pytest_asyncio.fixture
async def mock_telegram_user_client():
    """Create a mock Telethon client for testing."""
    return create_mock_telethon()

@pytest_asyncio.fixture
async def bot_transport(mock_telegram_bot):
    """Create a bot transport instance."""
    transport = TelegramBotTransport(token="test_token")
    transport._app = mock_telegram_bot
    transport._bot = mock_telegram_bot.bot
    transport._initialized = True  # Since we're mocking, we can set this directly
    return transport

@pytest_asyncio.fixture
async def user_transport(mock_telegram_user_client):
    """Create a user transport instance."""
    transport = TelegramUserTransport(
        api_id=123456789,
        api_hash="test_hash",
        phone_number="+1234567890"
    )
    transport._client = mock_telegram_user_client
    transport._initialized = True  # Since we're mocking, we can set this directly
    return transport

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_interaction")
async def test_telegram_interaction(bot_transport, user_transport):
    """Test interaction between bot and user transports."""
    logger.info("Starting telegram interaction test")

    # Start both transports
    await bot_transport.start()
    await user_transport.start()

    try:
        # Send message from user to bot
        frame = TextFrame(content="Hello bot!")
        frame.metadata["chat_id"] = 123456789
        await user_transport.send(frame)

        # Send message from bot to user
        frame = TextFrame(content="Hello user!")
        frame.metadata["chat_id"] = 123456789
        await bot_transport.send(frame)

    finally:
        # Stop both transports
        await bot_transport.stop()
        await user_transport.stop() 