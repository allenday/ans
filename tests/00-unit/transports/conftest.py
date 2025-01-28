"""Fixtures for transport tests."""
from tests.mocks.transports.telegram import bot_transport, mock_telegram_bot
from tests.mocks.transports.telethon import user_transport, mock_telegram_user_client

# Re-export the fixtures
__all__ = [
    'bot_transport',
    'mock_telegram_bot',
    'user_transport',
    'mock_telegram_user_client'
] 