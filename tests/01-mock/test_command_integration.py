"""Mock integration tests for command handling system."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from chronicler.commands.frames import CommandFrame
from chronicler.commands.processor import CommandProcessor
from chronicler.commands.handlers import (
    StartCommandHandler,
    ConfigCommandHandler,
    StatusCommandHandler
)
from chronicler.storage.interface import User
from chronicler.pipeline import Frame

class TestCommandIntegration:
    """Test command handling integration."""
    
    @pytest.fixture
    def storage(self):
        """Create a mock storage coordinator."""
        storage = Mock()
        storage.init_storage = AsyncMock()
        storage.set_github_config = AsyncMock()
        storage.sync = AsyncMock()
        storage.repo_path = Path("/test")
        return storage
    
    @pytest.fixture
    def processor(self, storage):
        """Create a command processor with handlers."""
        processor = CommandProcessor()
        processor.register_handler("/start", StartCommandHandler(storage))
        processor.register_handler("/config", ConfigCommandHandler(storage))
        processor.register_handler("/status", StatusCommandHandler(storage))
        return processor
    
    @pytest.mark.asyncio
    async def test_start_command_flow(self, processor, storage):
        """Test complete /start command flow."""
        # Create command frame
        frame = CommandFrame(
            command="/start",
            args=[],
            metadata={
                'sender_id': 123,
                'sender_name': 'test_user',
                'chat_id': 456,
                'chat_title': 'Test Chat'
            }
        )
        
        # Process command
        processor.push_frame = AsyncMock()
        await processor.process_frame(frame)
        
        # Verify storage initialization
        assert storage.init_storage.called
        user = storage.init_storage.call_args[0][0]
        assert isinstance(user, User)
        assert user.id == 123
        assert user.name == 'test_user'
        
        # Verify response
        assert processor.push_frame.called
        response = processor.push_frame.call_args[0][0]
        assert isinstance(response, Frame)
        assert "Welcome to Chronicler" in response.text
        assert "/config" in response.text
    
    @pytest.mark.asyncio
    async def test_config_command_flow(self, processor, storage):
        """Test complete /config command flow."""
        # Create command frame
        frame = CommandFrame(
            command="/config",
            args=["user/repo", "token123"],
            metadata={
                'sender_id': 123,
                'sender_name': 'test_user',
                'chat_id': 456
            }
        )
        
        # Process command
        processor.push_frame = AsyncMock()
        await processor.process_frame(frame)
        
        # Verify GitHub configuration
        storage.set_github_config.assert_called_with("token123", "user/repo")
        assert storage.sync.called
        
        # Verify response
        assert processor.push_frame.called
        response = processor.push_frame.call_args[0][0]
        assert isinstance(response, Frame)
        assert "Repository configured successfully" in response.text
        assert "user/repo" in response.text
    
    @pytest.mark.asyncio
    async def test_status_command_flow(self, processor, storage):
        """Test complete /status command flow."""
        # Create command frame
        frame = CommandFrame(
            command="/status",
            args=[],
            metadata={
                'sender_id': 123,
                'sender_name': 'test_user',
                'chat_id': 456
            }
        )
        
        # Mock metadata file
        metadata = {
            'user': {'name': 'test_user', 'id': 123},
            'github': {'repo': 'user/repo'},
            'stats': {
                'messages': 10,
                'media': 5,
                'last_sync': '2024-01-06T12:00:00'
            }
        }
        
        # Process command
        processor.push_frame = AsyncMock()
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open'), \
             patch('yaml.safe_load', return_value=metadata):
            await processor.process_frame(frame)
        
        # Verify response
        assert processor.push_frame.called
        response = processor.push_frame.call_args[0][0]
        assert isinstance(response, Frame)
        assert "Current Status" in response.text
        assert "test_user" in response.text
        assert "user/repo" in response.text
        assert "Messages: 10" in response.text
    
    @pytest.mark.asyncio
    async def test_error_handling_flow(self, processor, storage):
        """Test error handling in command flow."""
        # Make storage operations fail
        storage.init_storage.side_effect = Exception("Storage error")
        
        # Create command frame
        frame = CommandFrame(
            command="/start",
            args=[],
            metadata={
                'sender_id': 123,
                'sender_name': 'test_user'
            }
        )
        
        # Process command
        processor.push_frame = AsyncMock()
        await processor.process_frame(frame)
        
        # Verify error response
        assert processor.push_frame.called
        response = processor.push_frame.call_args[0][0]
        assert isinstance(response, Frame)
        assert "Error" in response.text
        assert "Storage error" in response.text
    
    @pytest.mark.asyncio
    async def test_unknown_command_flow(self, processor):
        """Test handling of unknown commands."""
        # Create command frame
        frame = CommandFrame(
            command="/unknown",
            args=[],
            metadata={
                'sender_id': 123,
                'sender_name': 'test_user'
            }
        )
        
        # Process command
        processor.push_frame = AsyncMock()
        await processor.process_frame(frame)
        
        # Verify response
        assert processor.push_frame.called
        response = processor.push_frame.call_args[0][0]
        assert isinstance(response, Frame)
        assert "Unknown command" in response.text
        assert "/start" in response.text
        assert "/config" in response.text
        assert "/status" in response.text
    
    @pytest.mark.asyncio
    async def test_non_command_frame_flow(self, processor):
        """Test handling of non-command frames."""
        # Create regular frame
        frame = Frame(text="Not a command")
        
        # Process frame
        processor.push_frame = AsyncMock()
        await processor.process_frame(frame)
        
        # Verify no response was sent
        assert not processor.push_frame.called 