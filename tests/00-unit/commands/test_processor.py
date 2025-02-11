"""Tests for command processor."""
import pytest
from unittest.mock import Mock, AsyncMock

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

TEST_METADATA = {"chat_id": 123}

@pytest.fixture
def mock_handler_func():
    """Create a mock async handler function."""
    async def handler(frame):
        return TextFrame(content="test response", metadata=frame.metadata)
    return handler  # Return the function directly, not awaiting it

@pytest.fixture
def coordinator_mock():
    """Create a mock storage coordinator."""
    mock = AsyncMock()
    mock.is_initialized = AsyncMock(return_value=False)
    mock.init_storage = AsyncMock()
    mock.create_topic = AsyncMock()
    mock.configure = AsyncMock()
    mock.sync = AsyncMock()
    return mock

class TestCommandProcessor:
    """Tests for command processor."""
    
    def test_initialization(self, coordinator_mock):
        """Test processor initialization."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        assert isinstance(processor.handlers, dict)
        assert len(processor.handlers) == 0
        
    @pytest.mark.asyncio
    async def test_register_command_valid(self, mock_handler_func, coordinator_mock):
        """Test valid command registration with async function."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        processor.register_command("/start", mock_handler_func)
        assert "/start" in processor._handlers
        # Create a test frame and verify handler functionality
        test_frame = CommandFrame(command="/start", args=[], metadata={"chat_id": 123})
        response = await processor._handlers["/start"](test_frame)
        assert response is not None
        assert isinstance(response, Frame)
        
    def test_register_command_invalid_command(self, mock_handler_func, coordinator_mock):
        """Test command registration with invalid command name."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        with pytest.raises(ValueError, match="Command must start with '/'"):
            processor.register_command("start", mock_handler_func)
            
    def test_register_command_invalid_handler(self, coordinator_mock):
        """Test command registration with invalid handler."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        with pytest.raises(ValueError, match="Handler must be a callable"):
            processor.register_command("/start", None)
            
    def test_register_command_duplicate(self, mock_handler_func, coordinator_mock):
        """Test command registration with duplicate command."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        processor.register_command("/test", mock_handler_func)
        with pytest.raises(ValueError, match="Handler for command /test already registered"):
            processor.register_command("/test", mock_handler_func)
            
    @pytest.mark.asyncio
    async def test_process_non_command_frame(self, coordinator_mock):
        """Test processing non-command frame."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        frame = TextFrame(content="test")
        result = await processor.process(frame)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_process_unknown_command(self, coordinator_mock):
        """Test processing unknown command."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        frame = CommandFrame(command="/unknown", metadata=TEST_METADATA)
        with pytest.raises(ValueError, match="No handler registered for command /unknown"):
            await processor.process(frame)
            
    @pytest.mark.asyncio
    async def test_handler_error(self, coordinator_mock):
        """Test handler error."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        
        async def failing_handler(frame):
            raise RuntimeError("Test error")
            
        processor.register_command("/test", failing_handler)
        frame = CommandFrame(command="/test", metadata=TEST_METADATA)
        with pytest.raises(RuntimeError, match="Test error"):
            await processor.process(frame)

    @pytest.mark.asyncio
    async def test_process_valid_command(self, coordinator_mock):
        """Test processing a valid command."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        async def test_handler(frame):
            return TextFrame(content="Test command executed", metadata=frame.metadata)
        processor.register_command("/test", test_handler)
        frame = CommandFrame(command="/test", args="", metadata={"chat_id": 123})
        result = await processor.process(frame)
        assert isinstance(result, TextFrame)
        assert result.content == "Test command executed"

    @pytest.mark.asyncio
    async def test_default_start_command(self, coordinator_mock):
        """Test the default /start command."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        async def start_handler(frame):
            return TextFrame(content="Started", metadata=frame.metadata)
        processor.register_command("/start", start_handler)
        frame = CommandFrame(command="/start", args="", metadata={"chat_id": 123})
        result = await processor.process(frame)
        assert result.content == "Started"

    @pytest.mark.asyncio
    async def test_default_status_command(self, coordinator_mock):
        """Test the default /status command."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        async def status_handler(frame):
            return TextFrame(content="Status OK", metadata=frame.metadata)
        processor.register_command("/status", status_handler)
        frame = CommandFrame(command="/status", args="", metadata={"chat_id": 123})
        result = await processor.process(frame)
        assert result.content == "Status OK" 