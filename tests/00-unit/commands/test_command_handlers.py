"""Tests for command handlers."""
import pytest
from unittest.mock import Mock
from chronicler.commands.frames import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.commands.handlers import (
    CommandHandler,
    StartCommandHandler,
    ConfigCommandHandler,
    StatusCommandHandler
)

from tests.mocks.storage import coordinator_mock

class TestCommandHandler:
    """Test base command handler."""
    
    def test_init(self, coordinator_mock):
        """Test handler initialization."""
        handler = StartCommandHandler(coordinator_mock)
        assert handler.coordinator == coordinator_mock

class TestStartCommandHandler:
    """Test start command handler."""
    
    @pytest.mark.asyncio
    async def test_handle_success(self, coordinator_mock):
        """Test successful start command handling."""
        handler = StartCommandHandler(coordinator_mock)
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
        assert "Welcome to Chronicler!" in result.content
        coordinator_mock.init_storage.assert_called_once()
        coordinator_mock.create_topic.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_error(self, coordinator_mock):
        """Test error handling in start command."""
        coordinator_mock.init_storage.side_effect = RuntimeError("Test error")
        handler = StartCommandHandler(coordinator_mock)
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
    async def test_handle_missing_args(self, coordinator_mock):
        """Test config command with missing arguments."""
        handler = ConfigCommandHandler(coordinator_mock)
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
        assert "Usage: /config" in result.content
        coordinator_mock.set_github_config.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_success(self, coordinator_mock):
        """Test successful config command handling."""
        handler = ConfigCommandHandler(coordinator_mock)
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
        assert "GitHub configuration updated" in result.content
        coordinator_mock.set_github_config.assert_called_once_with(
            token="token123",
            repo="owner/repo"
        )
        coordinator_mock.sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_config_error(self, coordinator_mock):
        """Test error handling in config command."""
        coordinator_mock.set_github_config.side_effect = RuntimeError("Test error")
        handler = ConfigCommandHandler(coordinator_mock)
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
    async def test_handle_not_initialized(self, coordinator_mock):
        """Test status command when storage is not initialized."""
        coordinator_mock.is_initialized.return_value = False
        handler = StatusCommandHandler(coordinator_mock)
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
        assert "Storage not initialized" in result.content
        coordinator_mock.sync.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_success(self, coordinator_mock):
        """Test successful status command handling."""
        coordinator_mock.is_initialized.return_value = True
        handler = StatusCommandHandler(coordinator_mock)
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
        assert "Chronicler Status" in result.content
        coordinator_mock.sync.assert_called_once() 