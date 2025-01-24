"""Tests for command handlers."""
import pytest
from unittest.mock import Mock, AsyncMock
from chronicler.commands.handlers import (
    CommandHandler, StartCommandHandler,
    ConfigCommandHandler, StatusCommandHandler
)
from chronicler.commands.frames import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.exceptions import (
    CommandValidationError,
    CommandStorageError,
    CommandExecutionError
)

# Test metadata for all tests
TEST_METADATA = {
    "sender_id": "123",
    "sender_name": "test_user",
    "chat_id": "456",
    "type": "commandframe"
}

@pytest.fixture
def mock_storage():
    """Create a mock storage coordinator."""
    storage = Mock()
    storage.init_storage = AsyncMock()
    storage.create_topic = AsyncMock()
    storage.set_github_config = AsyncMock()
    storage.sync = AsyncMock()
    storage.is_initialized = AsyncMock(return_value=False)
    return storage

class TestStartCommandHandler:
    """Tests for StartCommandHandler."""
    
    @pytest.mark.asyncio
    async def test_start_command_success(self, mock_storage):
        """Test successful /start command handling."""
        handler = StartCommandHandler(mock_storage)
        frame = CommandFrame(command="/start", metadata=TEST_METADATA)
        
        response = await handler.handle(frame)
        
        mock_storage.init_storage.assert_called_once_with(TEST_METADATA["sender_id"])
        mock_storage.create_topic.assert_called_once_with("default", TEST_METADATA)
        
        assert isinstance(response, TextFrame)
        assert "Welcome to Chronicler!" in response.content
        assert "/config" in response.content
        assert response.metadata == TEST_METADATA
    
    @pytest.mark.asyncio
    async def test_start_command_already_initialized(self, mock_storage):
        """Test /start when already initialized."""
        handler = StartCommandHandler(mock_storage)
        frame = CommandFrame(command="/start", metadata=TEST_METADATA)
        
        mock_storage.is_initialized.return_value = True
        
        with pytest.raises(CommandValidationError, match="Storage is already initialized"):
            await handler.handle(frame)
        
        mock_storage.init_storage.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_start_command_storage_error(self, mock_storage):
        """Test /start with storage error."""
        handler = StartCommandHandler(mock_storage)
        frame = CommandFrame(command="/start", metadata=TEST_METADATA)
        
        mock_storage.init_storage.side_effect = Exception("Storage error")
        
        with pytest.raises(CommandStorageError, match="Failed to initialize storage"):
            await handler.handle(frame)

class TestConfigCommandHandler:
    """Tests for ConfigCommandHandler."""
    
    @pytest.mark.asyncio
    async def test_config_command_success(self, mock_storage):
        """Test successful /config command handling."""
        handler = ConfigCommandHandler(mock_storage)
        frame = CommandFrame(
            command="/config",
            args=["user/repo", "ghp_token123"],
            metadata=TEST_METADATA
        )
        
        response = await handler.handle(frame)
        
        mock_storage.set_github_config.assert_called_once_with(
            token="ghp_token123",
            repo="user/repo"
        )
        mock_storage.sync.assert_called_once()
        
        assert isinstance(response, TextFrame)
        assert "GitHub configuration updated!" in response.content
        assert "user/repo" in response.content
        assert response.metadata == TEST_METADATA
    
    @pytest.mark.asyncio
    async def test_config_command_missing_args(self, mock_storage):
        """Test /config command with missing arguments."""
        handler = ConfigCommandHandler(mock_storage)
        frame = CommandFrame(command="/config", args=[], metadata=TEST_METADATA)
        
        with pytest.raises(CommandValidationError, match="Usage: /config"):
            await handler.handle(frame)
        
        mock_storage.set_github_config.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_config_command_invalid_repo(self, mock_storage):
        """Test /config with invalid repository format."""
        handler = ConfigCommandHandler(mock_storage)
        frame = CommandFrame(
            command="/config",
            args=["invalid-repo", "ghp_token123"],
            metadata=TEST_METADATA
        )
        
        with pytest.raises(CommandValidationError, match="Repository must be in format"):
            await handler.handle(frame)
    
    @pytest.mark.asyncio
    async def test_config_command_invalid_token(self, mock_storage):
        """Test /config with invalid token format."""
        handler = ConfigCommandHandler(mock_storage)
        frame = CommandFrame(
            command="/config",
            args=["user/repo", "invalid-token"],
            metadata=TEST_METADATA
        )
        
        with pytest.raises(CommandValidationError, match="Token must be a GitHub Personal Access Token"):
            await handler.handle(frame)

class TestStatusCommandHandler:
    """Tests for StatusCommandHandler."""
    
    @pytest.mark.asyncio
    async def test_status_command_success(self, mock_storage):
        """Test /status command when storage is initialized."""
        handler = StatusCommandHandler(mock_storage)
        frame = CommandFrame(command="/status", metadata=TEST_METADATA)
        
        mock_storage.is_initialized.return_value = True
        
        response = await handler.handle(frame)
        
        mock_storage.is_initialized.assert_called_once()
        mock_storage.sync.assert_called_once()
        
        assert isinstance(response, TextFrame)
        assert "Storage: Initialized" in response.content
        assert "GitHub: Connected" in response.content
        assert response.metadata == TEST_METADATA
    
    @pytest.mark.asyncio
    async def test_status_command_not_initialized(self, mock_storage):
        """Test /status command when storage is not initialized."""
        handler = StatusCommandHandler(mock_storage)
        frame = CommandFrame(command="/status", metadata=TEST_METADATA)
        
        with pytest.raises(CommandValidationError, match="Storage not initialized"):
            await handler.handle(frame)
        
        mock_storage.sync.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_status_command_sync_error(self, mock_storage):
        """Test /status when sync fails."""
        handler = StatusCommandHandler(mock_storage)
        frame = CommandFrame(command="/status", metadata=TEST_METADATA)
        
        mock_storage.is_initialized.return_value = True
        mock_storage.sync.side_effect = Exception("Sync failed")
        
        with pytest.raises(CommandStorageError, match="Failed to sync repository"):
            await handler.handle(frame) 