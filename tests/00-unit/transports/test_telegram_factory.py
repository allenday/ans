"""Tests for Telegram transport factory."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chronicler.transports.telegram.transport.bot import TelegramBotTransport
from chronicler.transports.telegram_user_transport import TelegramUserTransport
from chronicler.transports.telegram_factory import TelegramTransportFactory

def test_create_bot_transport():
    """Test creating bot transport."""
    transport = TelegramTransportFactory.create_transport("test_token")
    assert isinstance(transport, TelegramBotTransport)
    assert transport._token == "test_token"

def test_create_bot_transport_empty_token():
    """Test creating bot transport with empty token."""
    with pytest.raises(ValueError, match="Bot token cannot be empty"):
        TelegramTransportFactory.create_transport("")

def test_create_user_transport():
    """Test creating user transport."""
    transport = TelegramTransportFactory.create_transport(
        api_id=123456,
        api_hash="test_hash",
        phone_number="+1234567890"
    )
    assert isinstance(transport, TelegramUserTransport)
    assert transport._api_id == 123456
    assert transport._api_hash == "test_hash"
    assert transport._phone_number == "+1234567890"
    assert transport._session_name == ":memory:"

def test_create_user_transport_with_session():
    """Test creating user transport with custom session name."""
    transport = TelegramTransportFactory.create_transport(
        api_id=123456,
        api_hash="test_hash",
        phone_number="+1234567890",
        session_name="test_session"
    )
    assert transport._session_name == "test_session"

def test_create_user_transport_empty_api_id():
    """Test creating user transport with empty API ID."""
    with pytest.raises(ValueError, match="API ID cannot be empty"):
        TelegramTransportFactory.create_transport(
            api_id=0,
            api_hash="test_hash",
            phone_number="+1234567890"
        )

def test_create_user_transport_empty_api_hash():
    """Test creating user transport with empty API hash."""
    with pytest.raises(ValueError, match="API hash cannot be empty"):
        TelegramTransportFactory.create_transport(
            api_id=123456,
            api_hash="",
            phone_number="+1234567890"
        )

def test_create_user_transport_empty_phone():
    """Test creating user transport with empty phone number."""
    with pytest.raises(ValueError, match="Phone number cannot be empty"):
        TelegramTransportFactory.create_transport(
            api_id=123456,
            api_hash="test_hash",
            phone_number=""
        ) 