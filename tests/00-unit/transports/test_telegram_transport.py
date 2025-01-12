"""Unit tests for telegram transport."""
import pytest
import telegram
from abc import ABC

from chronicler.transports.base import BaseTransport
from chronicler.transports.telegram import TelegramBotTransport, TelegramUserTransport

def test_transport_base_is_abstract():
    """Test that BaseTransport is an abstract base class."""
    assert issubclass(BaseTransport, ABC)

def test_user_transport_implements_base():
    """Test that TelegramUserTransport properly implements base class."""
    assert issubclass(TelegramUserTransport, BaseTransport)

def test_bot_transport_implements_base():
    """Test that TelegramBotTransport properly implements base class."""
    assert issubclass(TelegramBotTransport, BaseTransport)

def test_user_transport_initialization():
    """Test TelegramUserTransport initialization."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    assert transport.api_id == "123"
    assert transport.api_hash == "abc"
    assert transport.phone_number == "+1234567890"
    assert transport.client is not None

def test_bot_transport_initialization():
    """Test TelegramBotTransport initialization."""
    transport = TelegramBotTransport(token="BOT:TOKEN")
    
    assert transport.token == "BOT:TOKEN"
    assert transport.app is not None

def test_user_transport_validates_params():
    """Test TelegramUserTransport parameter validation."""
    with pytest.raises(ValueError, match="api_id must not be empty"):
        TelegramUserTransport(api_id="", api_hash="abc", phone_number="+1234567890")
    
    with pytest.raises(ValueError, match="api_hash must not be empty"):
        TelegramUserTransport(api_id="123", api_hash="", phone_number="+1234567890")
    
    with pytest.raises(ValueError, match="phone_number must not be empty"):
        TelegramUserTransport(api_id="123", api_hash="abc", phone_number="")

def test_bot_transport_validates_params():
    """Test TelegramBotTransport parameter validation."""
    with pytest.raises(ValueError, match="Token must not be empty"):
        TelegramBotTransport(token="") 