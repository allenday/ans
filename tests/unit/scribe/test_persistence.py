import pytest
from unittest.mock import Mock, AsyncMock
from chronicler.scribe.core import Scribe
from chronicler.scribe.interface import UserState
from chronicler.storage.json_config import JsonConfigStorage
from chronicler.storage.interface import StorageAdapter

@pytest.fixture
def mock_storage():
    """Mock the storage adapter"""
    storage = Mock(spec=StorageAdapter)
    storage.init_storage = AsyncMock()
    storage.create_topic = AsyncMock()
    return storage

@pytest.fixture
def mock_telegram_bot():
    """Mock the Telegram API interface"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file"""
    return tmp_path / "config.json"

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_state_persistence(temp_config_file, mock_storage, mock_telegram_bot, test_config, test_user):
    """Test that scribe state persists across restarts"""
    config_store = JsonConfigStorage(temp_config_file)

    # Create first scribe instance
    scribe1 = Scribe(test_config, mock_storage, mock_telegram_bot, config_store)
    await scribe1.start()

    # Set up some state
    await scribe1.enable_group(123, "test_topic")
    session = scribe1.get_user_session(456)
    session.state = UserState.AWAITING_GITHUB_TOKEN
    session.context["test"] = "value"

    # Stop scribe (saves state)
    await scribe1.stop()

    # Create new scribe instance
    scribe2 = Scribe(test_config, mock_storage, mock_telegram_bot, config_store)
    await scribe2.start()

    # Verify state was restored
    assert scribe2.get_group_config(123).topic_id == "test_topic"
    restored_session = scribe2.get_user_session(456)
    assert restored_session.state == UserState.AWAITING_GITHUB_TOKEN
    assert restored_session.context["test"] == "value"

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_config_persistence(temp_config_file, mock_storage, mock_telegram_bot, test_config, test_user):
    """Test that configuration persists"""
    config_store = JsonConfigStorage(temp_config_file)
    scribe = Scribe(test_config, mock_storage, mock_telegram_bot, config_store)

    # Set GitHub config
    scribe.config.github_token = "test_token"
    scribe.config.github_repo = "test/repo"
    await scribe.stop()

    # Create new instance
    new_scribe = Scribe(test_config, mock_storage, mock_telegram_bot, config_store)
    await new_scribe.start()

    assert new_scribe.config.github_token == "test_token"
    assert new_scribe.config.github_repo == "test/repo" 