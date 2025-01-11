import pytest
from chronicler.transports.telegram_factory import (
    TelegramTransportFactory,
    TelegramTransportBase,
    TelegramUserTransport,
    TelegramBotTransport
)

def test_factory_creates_user_transport():
    """Test factory creates TelegramUserTransport when api_id and api_hash are provided."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    assert isinstance(transport, TelegramUserTransport)
    assert transport.api_id == "123"
    assert transport.api_hash == "abc"
    assert transport.phone_number == "+1234567890"

def test_factory_creates_bot_transport():
    """Test factory creates TelegramBotTransport when bot_token is provided."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(bot_token="BOT:TOKEN")
    
    assert isinstance(transport, TelegramBotTransport)
    assert transport.token == "BOT:TOKEN"

def test_factory_raises_error_on_missing_params():
    """Test factory raises ValueError when no parameters are provided."""
    factory = TelegramTransportFactory()
    
    with pytest.raises(ValueError, match=r"Must provide either bot_token or \(api_id, api_hash, phone_number\)"):
        factory.create_transport()

def test_factory_raises_error_on_partial_user_params():
    """Test factory raises ValueError when only some user parameters are provided."""
    factory = TelegramTransportFactory()
    
    with pytest.raises(ValueError, match=r"Must provide either bot_token or \(api_id, api_hash, phone_number\)"):
        factory.create_transport(api_id="123")
    
    with pytest.raises(ValueError, match=r"Must provide either bot_token or \(api_id, api_hash, phone_number\)"):
        factory.create_transport(api_id="123", api_hash="abc")

def test_factory_raises_error_on_mixed_params():
    """Test factory raises ValueError when both bot and user parameters are provided."""
    factory = TelegramTransportFactory()
    
    with pytest.raises(ValueError, match="Cannot provide both bot_token and user credentials"):
        factory.create_transport(
            bot_token="BOT:TOKEN",
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890"
        ) 