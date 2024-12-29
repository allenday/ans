import pytest
from unittest.mock import Mock, AsyncMock
from telegram import Update, Message, Chat, User as TelegramUser
from chronicler.scribe.core import Scribe
from chronicler.scribe.interface import ScribeConfig, UserState, GroupConfig
from chronicler.storage.interface import StorageAdapter, User
from chronicler.storage.config_interface import ConfigStorageAdapter

# Mark all tests in this file
pytestmark = [
    pytest.mark.unit,
    pytest.mark.scribe
]

@pytest.fixture
def mock_config_store():
    """Mock config storage"""
    store = Mock(spec=ConfigStorageAdapter)
    store.load = AsyncMock(return_value={})
    store.save = AsyncMock()
    return store

@pytest.fixture
def mock_storage():
    storage = Mock(spec=StorageAdapter)
    storage.init_storage = AsyncMock()
    storage.enable_group = AsyncMock()
    return storage

@pytest.fixture
def mock_telegram_bot():
    """Mock the Telegram API interface"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_scribe_initialization(test_config, mock_storage, mock_telegram_bot, mock_config_store, test_user):
    """Test scribe initialization"""
    scribe = Scribe(test_config, mock_storage, mock_telegram_bot, mock_config_store)
    await scribe.start()
    
    mock_storage.init_storage.assert_called_once_with(test_user)
    assert scribe.is_running
    
    await scribe.stop()
    assert not scribe.is_running

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_scribe_shutdown(test_config, mock_storage, mock_telegram_bot, mock_config_store, test_user):
    """Test scribe shutdown"""
    scribe = Scribe(test_config, mock_storage, mock_telegram_bot, mock_config_store)
    await scribe.start()
    await scribe.stop()
    
    assert not scribe.is_running

@pytest.mark.unit
@pytest.mark.scribe
def test_user_session_management(test_config, mock_storage, mock_telegram_bot, mock_config_store):
    """Test user session management"""
    scribe = Scribe(test_config, mock_storage, mock_telegram_bot, mock_config_store)
    
    # Get new session
    session = scribe.get_user_session(123)
    assert session.user_id == 123
    assert session.state == UserState.IDLE
    assert not session.context
    
    # Get existing session
    same_session = scribe.get_user_session(123)
    assert same_session is session

@pytest.mark.unit
@pytest.mark.scribe
def test_group_config_management(test_config, mock_storage, mock_telegram_bot, mock_config_store):
    """Test group configuration management"""
    scribe = Scribe(test_config, mock_storage, mock_telegram_bot, mock_config_store)
    
    # Initially no config
    assert scribe.get_group_config(123) is None
    
    # Add group config
    group_config = GroupConfig(group_id=123, topic_id="test_topic")
    scribe.groups[123] = group_config
    
    # Get existing config
    same_config = scribe.get_group_config(123)
    assert same_config is group_config 