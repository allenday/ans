"""Unit tests for telegram transport."""
import pytest
from unittest.mock import patch, MagicMock
from chronicler.transports.base import BaseTransport
from chronicler.transports.telegram_factory import TelegramUserTransport, TelegramBotTransport

def test_transport_base_is_abstract():
    """Test that BaseTransport is abstract."""
    with pytest.raises(TypeError):
        BaseTransport()

def test_user_transport_implements_base():
    """Test that TelegramUserTransport implements BaseTransport."""
    assert issubclass(TelegramUserTransport, BaseTransport)

def test_bot_transport_implements_base():
    """Test that TelegramBotTransport implements BaseTransport."""
    assert issubclass(TelegramBotTransport, BaseTransport)

@patch('chronicler.transports.telegram_factory.TelegramClient')
def test_user_transport_initialization(mock_client):
    """Test TelegramUserTransport initialization."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name="test_session"
    )
    assert transport.api_id == "123"
    assert transport.api_hash == "abc"
    assert transport.phone_number == "+1234567890"
    assert transport.session_name == "test_session"

@patch('chronicler.transports.telegram_factory.Application')
def test_bot_transport_initialization(mock_app):
    """Test TelegramBotTransport initialization."""
    transport = TelegramBotTransport(token="123:abc")
    assert transport.token == "123:abc"

def test_user_transport_validates_params():
    """Test that TelegramUserTransport validates parameters."""
    with pytest.raises(ValueError, match="api_id must not be empty"):
        TelegramUserTransport(api_id="", api_hash="abc", phone_number="+1234567890", session_name="test")
    
    with pytest.raises(ValueError, match="api_hash must not be empty"):
        TelegramUserTransport(api_id="123", api_hash="", phone_number="+1234567890", session_name="test")
    
    with pytest.raises(ValueError, match="phone_number must not be empty"):
        TelegramUserTransport(api_id="123", api_hash="abc", phone_number="", session_name="test")
    
    with pytest.raises(ValueError, match="session_name must not be empty"):
        TelegramUserTransport(api_id="123", api_hash="abc", phone_number="+1234567890", session_name="")

def test_bot_transport_validates_params():
    """Test that TelegramBotTransport validates parameters."""
    with pytest.raises(ValueError, match="token must not be empty"):
        TelegramBotTransport(token="") 