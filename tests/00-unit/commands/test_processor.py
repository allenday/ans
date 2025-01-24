"""Tests for command processor."""
import pytest
from unittest.mock import Mock, AsyncMock

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame
from chronicler.commands.frames import CommandFrame
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
def mock_handler():
    """Create a mock command handler."""
    handler = Mock(spec=CommandHandler)
    handler.command = "/test"
    return handler

class TestCommandProcessor:
    """Tests for command processor."""
    
    def test_initialization(self):
        """Test processor initialization."""
        processor = CommandProcessor()
        assert isinstance(processor.handlers, dict)
        assert len(processor.handlers) == 0
        
    def test_register_handler_valid(self, mock_handler):
        """Test valid handler registration."""
        processor = CommandProcessor()
        mock_handler.command = "/test"
        processor.register_handler(mock_handler)
        assert "/test" in processor.handlers
        assert processor.handlers["/test"] == mock_handler
        
    def test_register_handler_invalid_command(self, mock_handler):
        """Test handler registration with invalid command."""
        processor = CommandProcessor()
        with pytest.raises(ValueError, match="Command must start with '/'"):
            processor.register_handler(command="test", handler=mock_handler)
            
    def test_register_handler_none(self):
        """Test handler registration with None handler."""
        processor = CommandProcessor()
        with pytest.raises(ValueError, match="Handler cannot be None"):
            processor.register_handler(command="/test", handler=None)
            
    def test_register_handler_invalid_type(self):
        """Test handler registration with invalid handler type."""
        processor = CommandProcessor()
        invalid_handler = object()
        with pytest.raises(ValueError, match="Handler must be an instance of CommandHandler"):
            processor.register_handler(command="/test", handler=invalid_handler)
            
    def test_register_handler_duplicate(self, mock_handler):
        """Test handler registration with duplicate command."""
        processor = CommandProcessor()
        handler1 = Mock(spec=CommandHandler)
        handler1.command = "/test"
        handler2 = Mock(spec=CommandHandler)
        handler2.command = "/test"
        processor.register_handler(handler1)
        with pytest.raises(ValueError, match="Handler for command /test already registered"):
            processor.register_handler(handler2)
            
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
    async def test_handler_error(self):
        """Test handler error."""
        processor = CommandProcessor()
        handler = Mock(spec=CommandHandler)
        handler.command = "/test"
        handler.handle = AsyncMock(side_effect=RuntimeError("Test error"))
        processor.register_handler(handler)
        frame = CommandFrame(command="/test")
        with pytest.raises(RuntimeError, match="Test error"):
            await processor.process(frame) 