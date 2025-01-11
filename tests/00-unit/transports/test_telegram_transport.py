"""Unit tests for telegram transport."""
import pytest
import telegram
from abc import ABC

from chronicler.transports.telegram_factory import (
    TelegramTransportBase,
    TelegramUserTransport,
    TelegramBotTransport
)

def test_transport_base_is_abstract():
    """Test that TelegramTransportBase is an abstract base class."""
    assert issubclass(TelegramTransportBase, ABC)
    
    # Verify abstract methods
    abstract_methods = TelegramTransportBase.__abstractmethods__
    assert "start" in abstract_methods
    assert "stop" in abstract_methods
    assert "process_frame" in abstract_methods
    assert "send" in abstract_methods

def test_user_transport_implements_base():
    """Test that TelegramUserTransport properly implements base class."""
    assert issubclass(TelegramUserTransport, TelegramTransportBase)
    
    # Verify all abstract methods are implemented
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    assert hasattr(transport, "start")
    assert hasattr(transport, "stop")
    assert hasattr(transport, "process_frame")
    assert hasattr(transport, "send")

def test_bot_transport_implements_base():
    """Test that TelegramBotTransport properly implements base class."""
    assert issubclass(TelegramBotTransport, TelegramTransportBase)
    
    # Verify all abstract methods are implemented
    transport = TelegramBotTransport(token="BOT:TOKEN")
    assert hasattr(transport, "start")
    assert hasattr(transport, "stop")
    assert hasattr(transport, "process_frame")
    assert hasattr(transport, "send")

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
    with pytest.raises(telegram.error.InvalidToken, match="You must pass the token you received from https://t.me/Botfather!"):
        TelegramBotTransport(token="") 