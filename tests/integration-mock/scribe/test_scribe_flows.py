import pytest
from unittest.mock import Mock, AsyncMock
from telegram import Update, Message, Chat, User
from chronicler.scribe.core import Scribe
from chronicler.scribe.interface import ScribeConfig, UserState
from chronicler.storage.interface import StorageAdapter
from chronicler.storage.config_interface import ConfigStorageAdapter
from datetime import datetime

@pytest.fixture
def mock_storage():
    """Create a mock storage adapter"""
    storage = Mock(spec=StorageAdapter)
    storage.save_message = AsyncMock()
    storage.create_topic = AsyncMock()
    storage.init_storage = AsyncMock()
    storage.set_github_config = AsyncMock()
    return storage

@pytest.fixture
def mock_telegram_bot():
    """Mock the Telegram API interface"""
    bot = Mock()
    bot.send_message = AsyncMock()
    return bot

@pytest.mark.integration
@pytest.mark.mock
@pytest.mark.asyncio
async def test_complete_github_setup_flow(mock_telegram_bot, mock_storage, mock_config_store, test_config):
    """Test complete GitHub setup flow"""
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=mock_telegram_bot, config_store=mock_config_store)
    user_id = test_config.admin_users[0]
    chat_id = 123
    
    # Step 1: Start setup
    update = create_message("/setup", user_id, chat_id)
    response = await scribe.handle_command(update)
    assert "Please provide your GitHub token" in response.text
    
    # Step 2: Provide token
    update = create_message("ghp_123token", user_id, chat_id)
    response = await scribe.handle_message(update)
    assert "Please provide your GitHub repository" in response.text
    
    # Step 3: Provide repo
    update = create_message("user/repo", user_id, chat_id)
    response = await scribe.handle_message(update)
    assert "GitHub configuration complete" in response.text
    
    # Verify storage configuration
    mock_storage.set_github_config.assert_called_with(
        token="ghp_123token",
        repo="user/repo"
    )

@pytest.mark.integration
@pytest.mark.mock
@pytest.mark.asyncio
async def test_group_message_handling(mock_telegram_bot, mock_storage, mock_config_store, test_config):
    """Test handling group messages"""
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=mock_telegram_bot, config_store=mock_config_store)
    chat_id = 456
    
    # Enable group monitoring
    await scribe.enable_group(
        group_id=chat_id,
        topic_id="test_group"
    )
    
    # Send a message
    update = create_message("Test message", 789, chat_id, chat_type="group")
    await scribe.handle_message(update)
    
    # Verify message was saved
    mock_storage.save_message.assert_called_once()

@pytest.mark.integration
@pytest.mark.mock
@pytest.mark.asyncio
async def test_message_filtering(mock_telegram_bot, mock_storage, mock_config_store, test_config):
    """Test message filtering in groups"""
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=mock_telegram_bot, config_store=mock_config_store)
    chat_id = 456
    
    # Enable group monitoring with filters
    await scribe.enable_group(
        group_id=chat_id,
        topic_id="test_group"
    )
    
    # Set up filters
    group_config = scribe.get_group_config(chat_id)
    group_config.filters = {
        "media_only": True,
        "min_length": 10
    }
    
    # Test message that should be filtered out
    update = create_message("short", 789, chat_id, chat_type="group")
    await scribe.handle_message(update)
    
    # Verify message was not saved
    mock_storage.save_message.assert_not_called()

def create_message(text, user_id, chat_id, chat_type="private"):
    """Helper to create mock message updates"""
    update = Mock(spec=Update)
    message = Mock(spec=Message)
    chat = Mock(spec=Chat)
    user = Mock(spec=User)
    
    user.id = user_id
    chat.id = chat_id
    chat.type = chat_type
    message.chat = chat
    message.from_user = user
    message.text = text
    message.message_id = 1  # Add required message ID
    message.date = datetime.utcnow()  # Add message date
    
    # Initialize media attributes to None
    message.photo = None
    message.video = None
    message.document = None
    message.sticker = None
    message.animation = None
    message.voice = None
    message.audio = None
    
    # Initialize forwarding attributes to None
    message.forward_from = None
    message.forward_date = None
    
    update.message = message
    
    return update 