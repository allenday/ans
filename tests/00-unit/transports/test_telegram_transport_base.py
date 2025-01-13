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
    mock_client_instance = AsyncMock()
    mock_client.return_value = mock_client_instance
    mock_client_instance.connect = AsyncMock()
    mock_client_instance.disconnect = AsyncMock()
    mock_client_instance.is_user_authorized = AsyncMock(return_value=True)
    mock_client_instance.start = AsyncMock()
    
    # Mock the on method to return a function that can be called with the command handler
    def mock_on(event):
        def register_handler(handler):
            return handler
        return register_handler
    mock_client_instance.on = mock_on

    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name="test_session"
    )

    await transport.start()
    assert transport._initialized is True
    mock_client_instance.connect.assert_called_once()
    mock_client_instance.is_user_authorized.assert_called_once()
    mock_client_instance.start.assert_called_once_with(phone="+1234567890")

    await transport.stop()
    assert transport._initialized is False
    mock_client_instance.disconnect.assert_called_once()

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_factory.Application')
async def test_bot_transport_start_stop(mock_app):
    """Test starting and stopping TelegramBotTransport."""
    transport = TelegramBotTransport(token="123:abc")

    mock_app_instance = AsyncMock()
    mock_builder = MagicMock()
    mock_builder.token.return_value = mock_builder
    mock_builder.build = AsyncMock(return_value=mock_app_instance)
    mock_app.builder.return_value = mock_builder

    await transport.start()
    assert transport._initialized is True
    assert mock_builder.token.called
    assert mock_builder.build.called

    await transport.stop()
    assert transport._initialized is False
    assert mock_app_instance.stop.called

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_factory.Application')
async def test_bot_transport_start_error(mock_app):
    """Test error handling during TelegramBotTransport start."""
    transport = TelegramBotTransport(token="123:abc")

    mock_builder = MagicMock()
    mock_builder.token.return_value = mock_builder
    mock_builder.build.side_effect = InvalidToken("Invalid token")
    mock_app.builder.return_value = mock_builder

    with pytest.raises(InvalidToken, match="Invalid token"):
        await transport.start()
    assert not transport._initialized

@pytest.mark.asyncio
@patch('chronicler.transports.telegram_factory.TelegramClient')
async def test_user_transport_start_error(mock_client):
    """Test error handling during TelegramUserTransport start."""
    mock_client_instance = AsyncMock()
    mock_client.return_value = mock_client_instance
    mock_client_instance.connect = AsyncMock(side_effect=ConnectionError("Connection failed"))
    mock_client_instance.is_user_authorized = AsyncMock(return_value=False)
    mock_client_instance.start = AsyncMock()

    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name="test_session"
    )

    with pytest.raises(ConnectionError, match="Connection failed"):
        await transport.start()

    assert transport._initialized is False
    mock_client_instance.connect.assert_called_once()
    mock_client_instance.is_user_authorized.assert_not_called()
    mock_client_instance.start.assert_not_called() 