"""Tests for command handlers."""
import pytest
from unittest.mock import Mock, AsyncMock
from chronicler.commands.frames import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.commands.handlers import (
    CommandHandler,
    StartCommandHandler,
    ConfigCommandHandler,
    StatusCommandHandler
)

class TestCommandHandler:
    """Test base command handler."""
    
    def test_init(self):
        """Test handler initialization."""
        coordinator = Mock()
        handler = StartCommandHandler(coordinator)
        assert handler.coordinator == coordinator

class TestStartCommandHandler:
    """Test start command handler."""
    
    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful start command handling."""
        coordinator = AsyncMock()
        handler = StartCommandHandler(coordinator)
        frame = CommandFrame(
            command="/start",
            metadata={
                "chat_id": 123,
                "sender_id": 456,
                "sender_name": "testuser"
            }
        )
        
        result = await handler.handle(frame)
        
        assert isinstance(result, TextFrame)
        assert "Welcome to Chronicler!" in result.text
        coordinator.init_storage.assert_called_once()
        coordinator.create_topic.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_error(self):
        """Test error handling in start command."""
        coordinator = AsyncMock()
        coordinator.init_storage.side_effect = RuntimeError("Test error")
        handler = StartCommandHandler(coordinator)
        frame = CommandFrame(
            command="/start",
            metadata={
                "chat_id": 123,
                "sender_id": 456,
                "sender_name": "testuser"
            }
        )
        
        with pytest.raises(RuntimeError):
            await handler.handle(frame)

class TestConfigCommandHandler:
    """Test config command handler."""
    
    @pytest.mark.asyncio
    async def test_handle_missing_args(self):
        """Test config command with missing arguments."""
        coordinator = AsyncMock()
        handler = ConfigCommandHandler(coordinator)
        frame = CommandFrame(
            command="/config",
            args=["url"],
            metadata={
                "chat_id": 123,
                "sender_id": 456,
                "sender_name": "testuser"
            }
        )
        
        result = await handler.handle(frame)
        assert isinstance(result, TextFrame)
        assert "Usage: /config" in result.text
        coordinator.set_github_config.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful config command handling."""
        coordinator = AsyncMock()
        handler = ConfigCommandHandler(coordinator)
        frame = CommandFrame(
            command="/config",
            args=["owner/repo", "token123"],
            metadata={
                "chat_id": 123,
                "sender_id": 456,
                "sender_name": "testuser"
            }
        )
        
        result = await handler.handle(frame)
        
        assert isinstance(result, TextFrame)
        assert "GitHub configuration updated" in result.text
        coordinator.set_github_config.assert_called_once_with(
            token="token123",
            repo="owner/repo"
        )
    
    @pytest.mark.asyncio
    async def test_handle_config_error(self):
        """Test error handling in config command."""
        coordinator = AsyncMock()
        coordinator.set_github_config.side_effect = RuntimeError("Test error")
        handler = ConfigCommandHandler(coordinator)
        frame = CommandFrame(
            command="/config",
            args=["owner/repo", "token123"],
            metadata={
                "chat_id": 123,
                "sender_id": 456,
                "sender_name": "testuser"
            }
        )
        
        with pytest.raises(RuntimeError):
            await handler.handle(frame)

class TestStatusCommandHandler:
    """Test status command handler."""
    
    @pytest.mark.asyncio
    async def test_handle_not_initialized(self):
        """Test status command when storage is not initialized."""
        coordinator = AsyncMock()
        coordinator.is_initialized.return_value = False
        coordinator.sync = AsyncMock()
        handler = StatusCommandHandler(coordinator)
        frame = CommandFrame(
            command="/status",
            metadata={
                "chat_id": 123,
                "sender_id": 456,
                "sender_name": "testuser"
            }
        )
        
        result = await handler.handle(frame)
        assert isinstance(result, TextFrame)
        assert "Storage not initialized" in result.text
        coordinator.sync.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful status command handling."""
        coordinator = AsyncMock()
        coordinator.is_initialized.return_value = True
        coordinator.sync = AsyncMock()
        handler = StatusCommandHandler(coordinator)
        frame = CommandFrame(
            command="/status",
            metadata={
                "chat_id": 123,
                "sender_id": 456,
                "sender_name": "testuser"
            }
        )
        
        result = await handler.handle(frame)
        
        assert isinstance(result, TextFrame)
        assert "Chronicler Status" in result.text
        coordinator.sync.assert_called_once() 