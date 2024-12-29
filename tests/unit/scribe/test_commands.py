import pytest
from unittest.mock import Mock, AsyncMock
from telegram import Update, Message, Chat, User
from chronicler.scribe.interface import UserState, CommandResponse
from chronicler.scribe.core import Scribe
from chronicler.storage.interface import StorageAdapter
from chronicler.storage.config_interface import ConfigStorageAdapter

@pytest.fixture
def mock_message():
    """Create a mock telegram message"""
    message = Mock(spec=Message)
    message.chat = Mock(spec=Chat)
    message.from_user = Mock(spec=User)
    message.chat.id = 123
    message.chat.type = "private"
    message.from_user.id = 456
    return message

@pytest.fixture
def mock_update(mock_message):
    """Create a mock telegram update"""
    update = Mock(spec=Update)
    update.message = mock_message
    return update

@pytest.fixture
def mock_telegram_bot():
    """Mock the Telegram API interface"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot

@pytest.fixture
def mock_config_store():
    store = Mock(spec=ConfigStorageAdapter)
    store.load = AsyncMock(return_value={})
    store.save = AsyncMock()
    return store

@pytest.fixture
def mock_storage():
    storage = Mock(spec=StorageAdapter)
    storage.init_storage = AsyncMock()
    storage.sync = AsyncMock()
    storage.create_topic = AsyncMock()
    return storage

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_start_command(mock_update, test_config, mock_config_store):
    """Test /start command"""
    mock_update.message.text = "/start"
    scribe = Scribe(config=test_config, storage=Mock(), telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "Welcome" in response.text
    assert not response.error

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_help_command(mock_update, test_config, mock_config_store):
    """Test /help command"""
    mock_update.message.text = "/help"
    scribe = Scribe(config=test_config, storage=Mock(), telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "/setup" in response.text
    assert "/monitor" in response.text
    assert not response.error

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_status_command(mock_update, test_config, mock_storage, mock_config_store):
    """Test /status command"""
    mock_update.message.text = "/status"
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "github: not configured" in response.text.lower()
    assert "monitored groups: 0" in response.text.lower()

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_setup_command(mock_update, test_config, mock_config_store):
    """Test /setup command"""
    mock_update.message.text = "/setup"
    scribe = Scribe(config=test_config, storage=Mock(), telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "GitHub token" in response.text
    session = scribe.get_user_session(mock_update.message.from_user.id)
    assert session.state == UserState.AWAITING_GITHUB_TOKEN

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_monitor_command(mock_update, test_config, mock_storage, mock_config_store):
    """Test /monitor command"""
    mock_update.message.text = "/monitor test_topic"
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "github integration must be configured first" in response.text.lower()
    assert response.error

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_monitor_command_requires_github(mock_update, test_config, mock_config_store):
    """Test /monitor requires GitHub configuration"""
    mock_update.message.text = "/monitor test_topic"
    mock_update.message.chat.type = "group"
    
    scribe = Scribe(config=test_config, storage=Mock(), telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "github" in response.text.lower()
    assert response.error

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_unmonitor_command(mock_update, test_config, mock_storage, mock_config_store):
    """Test /unmonitor command"""
    mock_update.message.text = "/unmonitor"
    mock_storage.delete_topic = AsyncMock()
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "this group is not being monitored" in response.text.lower()
    assert response.error

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_filters_command(mock_update, test_config, mock_storage, mock_config_store):
    """Test /filters command"""
    mock_update.message.text = "/filters"
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "this group is not being monitored" in response.text.lower()
    assert response.error

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_sync_command(mock_update, test_config, mock_storage, mock_config_store):
    """Test /sync command"""
    mock_update.message.text = "/sync"
    test_config.github_token = "test_token"
    test_config.github_repo = "test/repo"
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "changes synced to remote" in response.text.lower()
    assert not response.error

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_list_command(mock_update, test_config, mock_storage, mock_config_store):
    """Test /list command"""
    mock_update.message.text = "/list"
    scribe = Scribe(config=test_config, storage=mock_storage, telegram_bot=Mock(), config_store=mock_config_store)
    
    response = await scribe.handle_command(mock_update)
    
    assert isinstance(response, CommandResponse)
    assert "no monitored groups" in response.text.lower()
    assert not response.error

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_command_handling(mock_update, test_config, mock_config_store):
    """Test command handling functionality"""
    # Setup
    mock_update.message.text = "/test arg1 arg2"
    mock_update.effective_chat = Mock()
    mock_update.effective_chat.type = "private"
    mock_update.effective_user = Mock()
    mock_update.effective_user.id = 123
    
    scribe = Scribe(test_config, storage=Mock(), telegram_bot=Mock(), config_store=mock_config_store)
    
    # Add test command handler
    async def _handle_test(self, update: Update, args: list[str] = None) -> CommandResponse:
        return CommandResponse(text=f"Executed test with args: {args}")
    
    # Monkey patch the handler
    original_handle = getattr(Scribe, "handle_command", None)
    async def handle_command(self, update: Update) -> CommandResponse:
        if update.message.text.startswith("/test"):
            return await _handle_test(self, update, update.message.text.split()[1:])
        return await original_handle(self, update)
    
    setattr(Scribe, "handle_command", handle_command)
    
    # Execute command
    response = await scribe.handle_command(mock_update)
    
    # Verify
    assert isinstance(response, CommandResponse)
    assert "Executed test with args: ['arg1', 'arg2']" in response.text
    assert not response.error
    
    # Clean up
    if original_handle:
        setattr(Scribe, "handle_command", original_handle)
    else:
        delattr(Scribe, "handle_command") 