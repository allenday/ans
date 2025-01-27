"""Unit tests for command processor implementation."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.exceptions import (
    CommandError, CommandStorageError, CommandValidationError,
    CommandExecutionError
)
from tests.mocks.processors import TestCommandHandler, command_processor, storage
from chronicler.processors.command import CommandProcessor
from chronicler.storage.coordinator import StorageCoordinator

pytestmark = pytest.mark.asyncio

@pytest.fixture
def storage():
    """Create a mock storage coordinator."""
    storage = AsyncMock(spec=StorageCoordinator)
    storage.is_initialized = AsyncMock(return_value=False)
    storage.init_storage = AsyncMock()
    storage.create_topic = AsyncMock()
    storage.save_message = AsyncMock()
    return storage

@pytest.fixture
def command_processor(storage):
    """Create a command processor with mock storage."""
    return CommandProcessor(storage)

async def test_command_processor_init(command_processor):
    """Test command processor initialization."""
    assert command_processor is not None
    assert isinstance(command_processor, CommandProcessor)

async def test_register_handler(command_processor):
    """Test registering a new command handler."""
    with patch('chronicler.processors.command.logger') as mock_logger:
        handler = TestCommandHandler()
        command_processor.register_handler("/test", handler)
        
        assert "/test" in command_processor.handlers
        assert command_processor.handlers["/test"] == handler
        mock_logger.debug.assert_called_with("PROC - Registered handler for /test")

async def test_process_non_command_frame(command_processor):
    """Test processing a non-command frame."""
    frame = TextFrame(content="not a command")
    result = await command_processor.process(frame)
    assert result is None

async def test_process_unknown_command(command_processor):
    """Test processing an unknown command."""
    frame = CommandFrame(command="/unknown", args="", metadata={"chat_id": 123})
    result = await command_processor.process(frame)
    assert isinstance(result, TextFrame)
    assert result.content == "Unknown command: /unknown"
    assert result.metadata == {"chat_id": 123, "type": "textframe"}

async def test_process_valid_command(command_processor):
    """Test processing a valid command."""
    handler = TestCommandHandler()
    command_processor.register_handler("/test", handler)
    
    frame = CommandFrame(command="/test", args="", metadata={"chat_id": 123})
    result = await command_processor.process(frame)
    
    assert isinstance(result, TextFrame)
    assert result.content == "test response"
    assert result.metadata["chat_id"] == 123

async def test_process_command_error(command_processor):
    """Test error handling during command processing."""
    async def failing_handle(frame):
        raise CommandExecutionError("Test error")
    
    handler = Mock()
    handler.handle.side_effect = failing_handle
    command_processor.register_handler("/fail", handler)
    
    frame = CommandFrame(command="/fail", args="", metadata={})
    
    with pytest.raises(CommandExecutionError, match="Test error"):
        await command_processor.process(frame)

async def test_default_start_command(command_processor, storage):
    """Test the default /start command."""
    frame = CommandFrame(command="/start", args="", metadata={"chat_id": 123})
    result = await command_processor.process(frame)

    assert result is not None
    assert result.content == "Storage initialized successfully! You can now configure your GitHub repository with /config."
    storage.is_initialized.assert_awaited_once()
    storage.init_storage.assert_awaited_once()
    storage.create_topic.assert_awaited_once()
    storage.save_message.assert_awaited_once_with(frame)

async def test_default_status_command(command_processor, storage):
    """Test the default /status command."""
    # Mock storage to be initialized
    storage.is_initialized = AsyncMock(return_value=True)
    storage.sync = AsyncMock()
    storage.get_topics = AsyncMock(return_value=["default"])
    storage.get_messages = AsyncMock(return_value=[{"text": "test"}])

    frame = CommandFrame(command="/status", args="", metadata={"chat_id": 123})
    result = await command_processor.process(frame)

    assert result.content == "Chronicler Status:\n- Storage: Initialized\n- GitHub: Connected\n- Last sync: Success"
    assert result.metadata == {"chat_id": 123, "type": "textframe"} 