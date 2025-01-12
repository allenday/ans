"""Unit tests for telegram transport."""
import pytest
import os
import uuid
from chronicler.transports.base import BaseTransport
from chronicler.transports.telegram_factory import TelegramUserTransport, TelegramBotTransport

def get_test_session():
    """Generate a unique session file name for tests."""
    return f"test_session_{uuid.uuid4()}.session"

def cleanup_session(session_name):
    """Clean up test session file."""
    if os.path.exists(session_name):
        os.remove(session_name)

@pytest.fixture
def session_file():
    """Fixture to manage test session file."""
    session = get_test_session()
    yield session
    cleanup_session(session)

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

def test_user_transport_initialization(session_file):
    """Test TelegramUserTransport initialization."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        session=session_file
    )
    assert transport.api_id == "123"
    assert transport.api_hash == "abc"
    assert transport.session == session_file

def test_bot_transport_initialization():
    """Test TelegramBotTransport initialization."""
    transport = TelegramBotTransport(token="123:abc")
    assert transport.token == "123:abc"

def test_user_transport_validates_params():
    """Test that TelegramUserTransport validates parameters."""
    with pytest.raises(ValueError):
        TelegramUserTransport(api_id=None, api_hash=None, session=None)

def test_bot_transport_validates_params():
    """Test that TelegramBotTransport validates parameters."""
    with pytest.raises(ValueError):
        TelegramBotTransport(token=None) 