"""Unit tests for telegram transport."""
import pytest
from unittest.mock import patch, MagicMock
from chronicler.transports.base import BaseTransport
from chronicler.transports.telegram_factory import TelegramUserTransport, TelegramBotTransport
import telegram
from telegram.error import InvalidToken
from unittest.mock import AsyncMock

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
    with pytest.raises(InvalidToken, match="You must pass the token you received from https://t.me/Botfather!"):
        TelegramBotTransport(None)
        
    with pytest.raises(InvalidToken, match="You must pass the token you received from https://t.me/Botfather!"):
        TelegramBotTransport("") 

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_factory.TelegramClient')
async def test_user_transport_start_stop(mock_client):
    """Test starting and stopping TelegramUserTransport."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name="test_session"
    )
    
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    mock_client_instance.start = AsyncMock()
    mock_client_instance.disconnect = AsyncMock()
    
    await transport.start()
    assert transport._initialized
    mock_client_instance.start.assert_called_once()
    
    await transport.stop()
    assert not transport._initialized
    mock_client_instance.disconnect.assert_called_once()

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_factory.Application')
async def test_bot_transport_start_stop(mock_app):
    """Test starting and stopping TelegramBotTransport."""
    transport = TelegramBotTransport(token="123:abc")
    
    mock_app_instance = MagicMock()
    mock_app.builder.return_value.token.return_value.build.return_value = mock_app_instance
    mock_app_instance.start = AsyncMock()
    mock_app_instance.stop = AsyncMock()
    
    await transport.start()
    assert transport._initialized
    mock_app_instance.start.assert_called_once()
    
    await transport.stop()
    assert not transport._initialized
    mock_app_instance.stop.assert_called_once()

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_factory.TelegramClient')
async def test_user_transport_start_error(mock_client):
    """Test error handling during TelegramUserTransport start."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name="test_session"
    )
    
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    mock_client_instance.start = AsyncMock(side_effect=Exception("Connection failed"))
    
    with pytest.raises(Exception, match="Connection failed"):
        await transport.start()
    assert not transport._initialized

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_factory.Application')
async def test_bot_transport_start_error(mock_app):
    """Test error handling during TelegramBotTransport start."""
    transport = TelegramBotTransport(token="123:abc")
    
    mock_app.builder.return_value.token.return_value.build.side_effect = InvalidToken("Invalid token")
    
    with pytest.raises(InvalidToken, match="Invalid token"):
        await transport.start()
    assert not transport._initialized 