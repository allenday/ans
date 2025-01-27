"""Tests for command processor."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Optional
import asyncio

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

@pytest.fixture
def coordinator_mock():
    return MagicMock()

@pytest.fixture
def command_processor(coordinator_mock):
    return CommandProcessor(coordinator=coordinator_mock)

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
        # Create a test frame
        test_frame = CommandFrame(command="/test", args=[], metadata={"chat_id": 123})
        # Run the handler and check the response
        response = asyncio.run(processor.handlers["/test"](test_frame))
        assert isinstance(response, TextFrame)
        assert response.content == "test response"
        assert response.metadata == test_frame.metadata
        
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
            command_processor.complete(frame.metadata["chat_id"])  # Complete command after successful config
            return TextFrame(content="GitHub configuration updated!", metadata=frame.metadata)
        else:
            # Handle text frame input
            repo, token = frame.content.split()
            await storage.set_github_config(repo, token)
            command_processor.complete(frame.metadata["chat_id"])  # Complete command after successful config
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

    # Verify config updated and context cleared
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
        command_processor.complete(frame.metadata["chat_id"])  # Complete command after status check
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
async def test_command_context_auto_replacement(command_processor):
    """Test that starting a new command automatically replaces any existing command context."""
    # Register test commands
    async def first_handler(frame):
        return TextFrame(content="First command response", metadata=frame.metadata)
        
    async def second_handler(frame):
        return TextFrame(content="Second command response", metadata=frame.metadata)
        
    command_processor.register_command("/first", first_handler)
    command_processor.register_command("/second", second_handler)
    
    # Start first command
    frame = CommandFrame(command="/first", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(frame)
    
    # Verify first context is open
    assert response.content == "First command response"
    assert command_processor.get_active_command(123) == "/first"
    
    # Start second command without explicitly closing first
    frame = CommandFrame(command="/second", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(frame)
    
    # Verify second command replaced first context
    assert response.content == "Second command response"
    assert command_processor.get_active_command(123) == "/second"
    
    # Verify no other contexts are open
    assert len(command_processor._active_commands) == 1

@pytest.mark.asyncio
async def test_command_explicit_context_closure(command_processor):
    """Test that a command can explicitly close its context."""
    # Register test command
    async def config_handler(frame):
        if isinstance(frame, CommandFrame):
            return TextFrame(content="Enter config value", metadata=frame.metadata)
        # Process input and explicitly close context
        command_processor.complete(frame.metadata["chat_id"])
        return TextFrame(content=f"Config set to: {frame.content}", metadata=frame.metadata)
        
    command_processor.register_command("/config", config_handler)
    
    # Start config command
    frame = CommandFrame(command="/config", args=[], metadata={"chat_id": 123})
    response = await command_processor.process(frame)
    
    # Verify context is open
    assert response.content == "Enter config value"
    assert command_processor.get_active_command(123) == "/config"
    
    # Send config value
    frame = TextFrame(content="test_value", metadata={"chat_id": 123})
    response = await command_processor.process(frame)
    
    # Verify context was closed by handler
    assert response.content == "Config set to: test_value"
    assert command_processor.get_active_command(123) is None
    
    # Verify no contexts are open
    assert len(command_processor._active_commands) == 0

@pytest.mark.asyncio
async def test_command_context_isolation(command_processor):
    """Test that command contexts are isolated between different chats."""
    # Register test command
    async def test_handler(frame):
        return TextFrame(content="Test response", metadata=frame.metadata)
        
    command_processor.register_command("/test", test_handler)
    
    # Start command in first chat
    frame = CommandFrame(command="/test", args=[], metadata={"chat_id": 123})
    await command_processor.process(frame)
    
    # Start command in second chat
    frame = CommandFrame(command="/test", args=[], metadata={"chat_id": 456})
    await command_processor.process(frame)
    
    # Verify both contexts are maintained separately
    assert command_processor.get_active_command(123) == "/test"
    assert command_processor.get_active_command(456) == "/test"
    assert len(command_processor._active_commands) == 2

@pytest.mark.asyncio
async def test_command_context_error_handling(command_processor):
    """Test that command context is properly cleared on errors."""
    # Register test command that raises an error
    async def error_handler(frame):
        raise RuntimeError("Test error")
        
    command_processor.register_command("/error", error_handler)
    
    # Start command that will error
    frame = CommandFrame(command="/error", args=[], metadata={"chat_id": 123})
    
    # Verify error is raised and context is cleared
    with pytest.raises(RuntimeError, match="Test error"):
        await command_processor.process(frame)
    
    assert command_processor.get_active_command(123) is None
    assert len(command_processor._active_commands) == 0

@pytest.mark.asyncio
async def test_command_no_nesting(command_processor, storage):
    """Test that starting a new command replaces the current context instead of nesting."""
    # Register test commands
    async def first_handler(frame):
        return TextFrame(content="Please provide first data", metadata=frame.metadata)

    async def second_handler(frame):
        command_processor.complete(frame.metadata["chat_id"])  # Explicitly complete command
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