"""Unit tests for CommandProcessor."""
import pytest
from unittest.mock import Mock, AsyncMock
from chronicler.commands.processor import CommandProcessor
from chronicler.commands.frames import CommandFrame
from chronicler.pipeline import Frame

def test_command_processor_init():
    """Test CommandProcessor initialization."""
    processor = CommandProcessor()
    assert processor._handlers == {}

def test_register_handler():
    """Test registering command handlers."""
    processor = CommandProcessor()
    handler = Mock()
    
    processor.register_handler("/test", handler)
    assert "/test" in processor._handlers
    assert processor._handlers["/test"] == handler

def test_register_handler_duplicate():
    """Test registering duplicate handlers."""
    processor = CommandProcessor()
    handler1 = Mock()
    handler2 = Mock()
    
    processor.register_handler("/test", handler1)
    processor.register_handler("/test", handler2)
    assert processor._handlers["/test"] == handler2  # Last one wins

def test_register_handler_validation():
    """Test handler registration validation."""
    processor = CommandProcessor()
    
    # Command must start with /
    with pytest.raises(ValueError):
        processor.register_handler("test", Mock())
    
    # Handler must not be None
    with pytest.raises(ValueError):
        processor.register_handler("/test", None)

@pytest.mark.asyncio
async def test_process_non_command_frame():
    """Test processing non-command frames."""
    processor = CommandProcessor()
    frame = Frame(text="test")  # Regular frame, not a command
    
    # Should be ignored
    await processor.process_frame(frame)
    # No assertions needed - if it doesn't raise, it passed

@pytest.mark.asyncio
async def test_process_unknown_command():
    """Test processing unknown commands."""
    processor = CommandProcessor()
    processor.push_frame = AsyncMock()
    
    frame = CommandFrame(
        command="/unknown",
        args=[],
        metadata={}
    )
    
    await processor.process_frame(frame)
    
    # Should send error response
    assert processor.push_frame.called
    response = processor.push_frame.call_args[0][0]
    assert "Unknown command" in response.text

@pytest.mark.asyncio
async def test_handler_error():
    """Test handling errors from command handlers."""
    processor = CommandProcessor()
    processor.push_frame = AsyncMock()
    
    # Create handler that raises an exception
    handler = Mock()
    handler.handle = AsyncMock(side_effect=Exception("Test error"))
    processor.register_handler("/test", handler)
    
    frame = CommandFrame(
        command="/test",
        args=[],
        metadata={}
    )
    
    await processor.process_frame(frame)
    
    # Should send error response
    assert processor.push_frame.called
    response = processor.push_frame.call_args[0][0]
    assert "Error" in response.text 