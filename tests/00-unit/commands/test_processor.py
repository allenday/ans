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

class TestCommandProcessor:
    """Tests for command processor."""
    
    def test_initialization(self):
        """Test processor initialization."""
        processor = CommandProcessor()
        assert isinstance(processor.handlers, dict)
        assert len(processor.handlers) == 0
        
    @pytest.mark.asyncio
    async def test_register_command_valid(self, mock_handler_func):
        """Test valid command registration with async function."""
        processor = CommandProcessor()
        processor.register_command("/start", mock_handler_func)
        assert "/start" in processor._handlers
        assert processor._handlers["/start"] == mock_handler_func
        
        # Test the handler works
        frame = CommandFrame(command="/start", metadata=TEST_METADATA)
        response = await processor.process(frame)
        assert isinstance(response, TextFrame)
        assert response.content == "test response"
        assert response.metadata == TEST_METADATA
        
    def test_register_command_invalid_command(self, mock_handler_func):
        """Test command registration with invalid command name."""
        processor = CommandProcessor()
        with pytest.raises(ValueError, match="Command must start with '/'"):
            processor.register_command("start", mock_handler_func)
            
    def test_register_command_invalid_handler(self):
        """Test command registration with invalid handler."""
        processor = CommandProcessor()
        with pytest.raises(ValueError, match="Handler must be a callable"):
            processor.register_command("/start", None)
            
    def test_register_command_duplicate(self, mock_handler_func):
        """Test command registration with duplicate command."""
        processor = CommandProcessor()
        processor.register_command("/test", mock_handler_func)
        with pytest.raises(ValueError, match="Handler for command /test already registered"):
            processor.register_command("/test", mock_handler_func)
            
    @pytest.mark.asyncio
    async def test_process_non_command_frame(self):
        """Test processing non-command frame."""
        processor = CommandProcessor()
        frame = TextFrame(content="test")
        result = await processor.process(frame)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_process_unknown_command(self):
        """Test processing unknown command."""
        processor = CommandProcessor()
        frame = CommandFrame(command="/unknown")
        with pytest.raises(ValueError, match="No handler registered for command /unknown"):
            await processor.process(frame)
            
    @pytest.mark.asyncio
    async def test_handler_error(self, mock_handler_func):
        """Test handler error."""
        processor = CommandProcessor()
        
        async def failing_handler(frame):
            raise RuntimeError("Test error")
            
        processor.register_command("/test", failing_handler)
        frame = CommandFrame(command="/test")
        with pytest.raises(RuntimeError, match="Test error"):
            await processor.process(frame) 