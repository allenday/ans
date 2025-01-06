"""Unit tests for command handlers."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from chronicler.commands.frames import CommandFrame
from chronicler.commands.handlers import (
    CommandHandler,
    StartCommandHandler,
    ConfigCommandHandler,
    StatusCommandHandler
)
from chronicler.storage.interface import User

class TestCommandHandler:
    """Test base command handler."""
    
    def test_init(self):
        """Test handler initialization."""
        storage = Mock()
        # Create a concrete subclass for testing
        class TestHandler(CommandHandler):
            async def handle(self, frame: CommandFrame) -> str:
                return "test"
        
        handler = TestHandler(storage)
        assert handler.storage == storage

class TestStartCommandHandler:
    """Test start command handler."""
    
    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful start command."""
        # Arrange
        storage = Mock()
        storage.init_storage = AsyncMock()
        handler = StartCommandHandler(storage)
        
        frame = CommandFrame(
            command="/start",
            args=[],
            metadata={
                'sender_id': 123,
                'sender_name': 'test_user'
            }
        )
        
        # Act
        response = await handler.handle(frame)
        
        # Assert
        assert storage.init_storage.called
        user = storage.init_storage.call_args[0][0]
        assert isinstance(user, User)
        assert user.id == 123
        assert user.name == 'test_user'
        assert "Welcome to Chronicler" in response

    @pytest.mark.asyncio
    async def test_handle_error(self):
        """Test start command with storage error."""
        # Arrange
        storage = Mock()
        storage.init_storage = AsyncMock(side_effect=Exception("Test error"))
        handler = StartCommandHandler(storage)
        
        frame = CommandFrame(
            command="/start",
            args=[],
            metadata={
                'sender_id': 123,
                'sender_name': 'test_user'
            }
        )
        
        # Act & Assert
        with pytest.raises(Exception):
            await handler.handle(frame)

class TestConfigCommandHandler:
    """Test config command handler."""
    
    @pytest.mark.asyncio
    async def test_handle_missing_args(self):
        """Test config command with missing arguments."""
        # Arrange
        handler = ConfigCommandHandler(Mock())
        frame = CommandFrame(
            command="/config",
            args=[],
            metadata={'sender_id': 123}
        )
        
        # Act
        response = await handler.handle(frame)
        
        # Assert
        assert "Invalid configuration format" in response

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful config command."""
        # Arrange
        storage = Mock()
        storage.set_github_config = AsyncMock()
        storage.sync = AsyncMock()
        handler = ConfigCommandHandler(storage)
        
        frame = CommandFrame(
            command="/config",
            args=["user/repo", "token123"],
            metadata={'sender_id': 123}
        )
        
        # Act
        response = await handler.handle(frame)
        
        # Assert
        storage.set_github_config.assert_called_with("token123", "user/repo")
        assert storage.sync.called
        assert "Repository configured successfully" in response

    @pytest.mark.asyncio
    async def test_handle_config_error(self):
        """Test config command with configuration error."""
        # Arrange
        storage = Mock()
        storage.set_github_config = AsyncMock(side_effect=Exception("Test error"))
        handler = ConfigCommandHandler(storage)
        
        frame = CommandFrame(
            command="/config",
            args=["user/repo", "token123"],
            metadata={'sender_id': 123}
        )
        
        # Act
        response = await handler.handle(frame)
        
        # Assert
        assert "Failed to configure repository" in response

class TestStatusCommandHandler:
    """Test status command handler."""
    
    @pytest.mark.asyncio
    async def test_handle_not_initialized(self):
        """Test status command when bot is not initialized."""
        # Arrange
        storage = Mock()
        storage.repo_path = Path("/test")
        handler = StatusCommandHandler(storage)
        
        frame = CommandFrame(
            command="/status",
            args=[],
            metadata={'sender_id': 123}
        )
        
        # Act
        with patch('pathlib.Path.exists', return_value=False):
            response = await handler.handle(frame)
        
        # Assert
        assert "Bot not initialized" in response

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful status command."""
        # Arrange
        storage = Mock()
        storage.repo_path = Path("/test")
        handler = StatusCommandHandler(storage)
        
        frame = CommandFrame(
            command="/status",
            args=[],
            metadata={'sender_id': 123}
        )
        
        metadata = {
            'user': {'name': 'test_user', 'id': 123},
            'github': {'repo': 'user/repo'},
            'stats': {
                'messages': 10,
                'media': 5,
                'last_sync': '2024-01-06T12:00:00'
            }
        }
        
        # Act
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open'), \
             patch('yaml.safe_load', return_value=metadata):
            response = await handler.handle(frame)
        
        # Assert
        assert "Current Status" in response
        assert "test_user" in response
        assert "user/repo" in response
        assert "Messages: 10" in response 