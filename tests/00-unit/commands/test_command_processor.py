"""Tests for command processor."""
import pytest
from unittest.mock import Mock, AsyncMock

from chronicler.frames.media import TextFrame
from chronicler.frames.command import CommandFrame
from chronicler.commands.processor import CommandProcessor
from chronicler.handlers.command import CommandHandler
from chronicler.exceptions import CommandError

from tests.mocks.storage import coordinator_mock

TEST_METADATA = {"chat_id": 123}

class TestCommandProcessor:
    """Test command processor."""
    
    def test_init(self, coordinator_mock):
        """Test initialization."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        assert processor.handlers == {}
        
    def test_register_handler(self, coordinator_mock):
        """Test registering a handler."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        handler = Mock(spec=CommandHandler)
        handler.command = "/test"
        processor.register_handler(handler)
        assert "/test" in processor.handlers
        assert processor.handlers["/test"] == handler
        
    def test_register_handler_duplicate(self, coordinator_mock):
        """Test registering a duplicate handler."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        handler1 = Mock(spec=CommandHandler)
        handler1.command = "/test"
        handler2 = Mock(spec=CommandHandler)
        handler2.command = "/test"
        
        processor.register_handler(handler1)
        with pytest.raises(ValueError, match="Handler for command /test already registered"):
            processor.register_handler(handler2)
            
    def test_register_handler_validation(self, coordinator_mock):
        """Test handler registration validation."""
        processor = CommandProcessor(coordinator=coordinator_mock)
        
        with pytest.raises(ValueError, match="Handler cannot be None"):
            processor.register_handler(None)
            
        with pytest.raises(ValueError, match="Handler must be an instance of CommandHandler"):
            processor.register_handler(Mock())
            
        handler = Mock(spec=CommandHandler)
        handler.command = None
        with pytest.raises(ValueError, match="Handler must have a command"):
            processor.register_handler(handler)
            
        handler.command = "test"
        with pytest.raises(ValueError, match="Command must start with '/'"):
            processor.register_handler(handler)
            
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
        handler = Mock(spec=CommandHandler)
        handler.command = "/test"
        handler.handle = AsyncMock(side_effect=RuntimeError("Test error"))
        processor.register_handler(handler)
        frame = CommandFrame(command="/test")
        with pytest.raises(RuntimeError, match="Test error"):
            await processor.process(frame) 