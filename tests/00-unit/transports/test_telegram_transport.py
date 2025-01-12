"""Unit tests for telegram transport."""
import pytest
import telegram
import os
import uuid
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

def test_bot_transport_initialization():
    """Test TelegramBotTransport initialization."""
    transport = TelegramBotTransport(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
    assert transport.token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

def test_user_transport_validates_params():
    """Test that TelegramUserTransport validates parameters."""
    with pytest.raises(ValueError, match="api_id must not be empty"):
        TelegramUserTransport(api_id="", api_hash="abc", phone_number="+1234567890")
    
    with pytest.raises(ValueError, match="api_hash must not be empty"):
        TelegramUserTransport(api_id="123", api_hash="", phone_number="+1234567890")
    
    with pytest.raises(ValueError, match="phone_number must not be empty"):
        TelegramUserTransport(api_id="123", api_hash="abc", phone_number="")

def test_bot_transport_validates_params():
    """Test that TelegramBotTransport validates parameters."""
    with pytest.raises(telegram.error.InvalidToken):
        TelegramBotTransport(token="") 