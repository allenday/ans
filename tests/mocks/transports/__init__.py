"""Mock implementations for Telegram transports."""

from .telegram import create_mock_telethon, MockUpdate

__all__ = ['create_mock_telethon', 'MockUpdate'] 