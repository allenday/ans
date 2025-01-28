"""Tests for telegram interaction."""
import pytest
import pytest_asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch
from telegram import Bot, Message, Chat, User, Update, PhotoSize
from telegram.ext import ApplicationBuilder, Application
from chronicler.frames import TextFrame
from chronicler.transports.telegram.transport.bot import TelegramBotTransport
from chronicler.transports.telegram.transport.user import TelegramUserTransport
from chronicler.logging.config import trace_operation
from tests.mocks.transports.telegram import bot_transport, mock_telegram_bot
from tests.mocks.transports.telethon import user_transport, mock_telegram_user_client
import asyncio
from chronicler.transports.events import EventMetadata

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
@trace_operation("test.transport.telegram_interaction")
async def test_telegram_interaction(bot_transport, user_transport):
    """Test interaction between bot and user transports."""
    logger.info("Starting telegram interaction test")

    try:
        # Send message from user to bot
        frame = TextFrame(content="Hello bot!")
        frame.metadata = EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=1,
            thread_id="default"
        )
        await user_transport.send(frame)
        user_transport._message_sender.send.assert_awaited_once()

        # Send message from bot to user
        frame = TextFrame(content="Hello user!")
        frame.metadata = EventMetadata(
            chat_id=123456789,
            chat_title="Test Chat",
            sender_id=987654321,
            sender_name="Test User",
            message_id=2,
            thread_id="default"
        )
        await bot_transport.send(frame)
        bot_transport._message_sender.send.assert_awaited_once()

    finally:
        # Stop both transports
        await bot_transport.stop()
        await user_transport.stop() 