"""Tests for command processor."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from typing import Optional

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame
from chronicler.frames.command import CommandFrame
from chronicler.handlers.command import CommandHandler
from chronicler.commands.processor import CommandProcessor
from chronicler.exceptions import (
    CommandError,
    CommandValidationError,
    CommandStorageError,
    CommandAuthorizationError
)

from tests.mocks.storage import coordinator_mock

TEST_METADATA = {"chat_id": 123}

@pytest.fixture
def mock_handler():
    """Create a mock command handler."""
    async def handler(frame):
        return TextFrame(content="test response", metadata=frame.metadata)
    return handler

@pytest_asyncio.fixture
async def storage():
    """Create a mock storage coordinator."""
    storage = AsyncMock()
    storage.is_initialized = AsyncMock(return_value=True)
    storage.set_github_config = AsyncMock()
    return storage

@pytest_asyncio.fixture
async def command_processor(storage):
    """Create a command processor for testing."""
    processor = CommandProcessor(coordinator=storage)
    # Clear any default handlers
    processor._handlers.clear()
    return processor

class TestCommandProcessor:
    """Test command processor."""
    
    def test_init(self, coordinator_mock):
        """Test initialization."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        assert processor.handlers == {}
        
    def test_register_handler(self, coordinator_mock):
        """Test registering a handler."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        async def handler(frame):
            return TextFrame(content="test response", metadata=frame.metadata)
        processor.register_command("/test", handler)
        assert "/test" in processor.handlers
        assert processor.handlers["/test"] == handler
        
    def test_register_handler_duplicate(self, coordinator_mock):
        """Test registering a duplicate handler."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        async def handler1(frame):
            return TextFrame(content="test response", metadata=frame.metadata)
        async def handler2(frame):
            return TextFrame(content="test response 2", metadata=frame.metadata)
        
        processor.register_command("/test", handler1)
        with pytest.raises(ValueError, match="Handler for command /test already registered"):
            processor.register_command("/test", handler2)
            
    def test_register_handler_validation(self, coordinator_mock):
        """Test handler registration validation."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        
        with pytest.raises(ValueError, match="Handler must be a callable"):
            processor.register_command("/test", None)
        
        with pytest.raises(ValueError, match="Command must start with '/'"):
            processor.register_command("test", mock_handler)
            
    @pytest.mark.asyncio
    async def test_process_non_command_frame(self, coordinator_mock):
        """Test processing a non-command frame."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        frame = TextFrame(content="test")
        assert await processor.process(frame) is None
        
    @pytest.mark.asyncio
    async def test_process_unknown_command(self, coordinator_mock):
        """Test processing an unknown command."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        frame = CommandFrame(command="/unknown")
        with pytest.raises(ValueError, match="No handler registered for command /unknown"):
            await processor.process(frame)
            
    @pytest.mark.asyncio
    async def test_handler_error(self, coordinator_mock):
        """Test handler error."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        
        async def failing_handler(frame):
            raise RuntimeError("Test error")
            
        processor.register_command("/test", failing_handler)
        frame = CommandFrame(command="/test")
        with pytest.raises(RuntimeError, match="Test error"):
            await processor.process(frame)

@pytest.mark.asyncio
async def test_stateful_command_flow(command_processor, storage):
    """Test a multi-step command flow with state."""
    # Register config handler
    async def config_handler(frame):
        if isinstance(frame, CommandFrame):
            if not frame.args:
                return TextFrame(content="Please provide your GitHub repository and token in the format: username/repo ghp_token", metadata=frame.metadata)
            repo, token = frame.args
            await storage.set_github_config(repo, token)
            return TextFrame(content="GitHub configuration updated!", metadata=frame.metadata)
        else:
            # Handle text frame input
            repo, token = frame.content.split()
            await storage.set_github_config(repo, token)
            return TextFrame(content="GitHub configuration updated!", metadata=frame.metadata)

    command_processor.register_command("/config", config_handler)

    # Initial command
    frame = CommandFrame(command="/config", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(frame)

    # Verify in config state
    assert response is not None
    assert response.content == "Please provide your GitHub repository and token in the format: username/repo ghp_token"
    assert command_processor.get_active_command(123) == "/config"

    # Send data
    frame = TextFrame(content="username/repo ghp_token", metadata={"chat_id": 123})
    response = await command_processor.process(frame)

    # Verify config updated
    assert response is not None
    assert response.content == "GitHub configuration updated!"
    assert command_processor.get_active_command(123) is None
    storage.set_github_config.assert_awaited_once_with("username/repo", "ghp_token")

@pytest.mark.asyncio
async def test_command_interruption(command_processor, storage):
    """Test interrupting a command flow with another command."""
    # Register handlers
    async def config_handler(frame):
        return TextFrame(content="Please provide your GitHub repository and token in the format: username/repo ghp_token", metadata=frame.metadata)

    async def status_handler(frame):
        return TextFrame(content="Status: All systems operational", metadata=frame.metadata)

    command_processor.register_command("/config", config_handler)
    command_processor.register_command("/status", status_handler)

    # Start config command
    frame = CommandFrame(command="/config", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(frame)

    # Verify in config state
    assert response is not None
    assert response.content == "Please provide your GitHub repository and token in the format: username/repo ghp_token"
    assert command_processor.get_active_command(123) == "/config"

    # Interrupt with status command
    interrupt_frame = CommandFrame(command="/status", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(interrupt_frame)

    # Verify status response and cleared state
    assert response is not None
    assert response.content == "Status: All systems operational"
    assert command_processor.get_active_command(123) is None
    
    # Verify original command data was not processed
    storage.set_github_config.assert_not_called()

@pytest.mark.asyncio
async def test_command_context_auto_closure(command_processor, storage):
    """Test that command context is automatically closed when command completes."""
    # Register test command
    async def test_handler(frame):
        if isinstance(frame, CommandFrame):
            return TextFrame(content="Please provide data", metadata=frame.metadata)
        else:
            # Process the data and return completion response
            return TextFrame(content="Command completed!", metadata=frame.metadata)

    command_processor.register_command("/test", test_handler)

    # Start command
    frame = CommandFrame(command="/test", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(frame)

    # Verify context is open
    assert response.content == "Please provide data"
    assert command_processor.get_active_command(123) == "/test"

    # Send data and complete command
    data_frame = TextFrame(content="test data", metadata={"chat_id": 123})
    response = await command_processor.process(data_frame)

    # Verify context is automatically closed
    assert response.content == "Command completed!"
    assert command_processor.get_active_command(123) is None

@pytest.mark.asyncio
async def test_command_no_nesting(command_processor, storage):
    """Test that starting a new command replaces the current context instead of nesting."""
    # Register test commands
    async def first_handler(frame):
        return TextFrame(content="Please provide first data", metadata=frame.metadata)

    async def second_handler(frame):
        return TextFrame(content="Second command complete", metadata=frame.metadata)

    command_processor.register_command("/first", first_handler)
    command_processor.register_command("/second", second_handler)

    # Start first command
    frame = CommandFrame(command="/first", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(frame)

    # Verify first context is open
    assert response.content == "Please provide first data"
    assert command_processor.get_active_command(123) == "/first"

    # Start second command without completing first
    frame = CommandFrame(command="/second", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(frame)

    # Verify second command replaced first context
    assert response.content == "Second command complete"
    assert command_processor.get_active_command(123) is None

    # Verify first command context was replaced by sending data for it
    data_frame = TextFrame(content="first data", metadata={"chat_id": 123})
    response = await command_processor.process(data_frame)

    # Should not be handled since first command context was replaced
    assert response is None 