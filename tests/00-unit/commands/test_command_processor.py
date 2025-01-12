"""Tests for command processor."""
import pytest
from unittest.mock import AsyncMock
from chronicler.commands.processor import CommandProcessor
from chronicler.commands.frames import CommandFrame
from chronicler.frames.media import TextFrame

from tests.mocks import command_handler_mock

@pytest.mark.asyncio
async def test_command_processor_init():
    """Test command processor initialization."""
    processor = CommandProcessor()
    assert len(processor._handlers) == 0  # No default handlers

@pytest.mark.asyncio
async def test_register_handler(command_handler_mock):
    """Test handler registration."""
    processor = CommandProcessor()
    
    processor.register_handler("/test", command_handler_mock)
    assert processor._handlers["/test"] == command_handler_mock

@pytest.mark.asyncio
async def test_register_handler_duplicate(command_handler_mock):
    """Test registering duplicate handler."""
    processor = CommandProcessor()
    handler1 = command_handler_mock
    handler2 = command_handler_mock
    
    processor.register_handler("/test", handler1)
    processor.register_handler("/test", handler2)
    assert processor._handlers["/test"] == handler2

@pytest.mark.asyncio
async def test_register_handler_validation():
    """Test handler registration validation."""
    processor = CommandProcessor()
    handler = AsyncMock()  # Not a CommandHandler
    
    with pytest.raises(ValueError):
        processor.register_handler("/test", handler)

@pytest.mark.asyncio
async def test_process_non_command_frame():
    """Test processing non-command frame."""
    processor = CommandProcessor()
    frame = TextFrame(text="test", metadata={})
    
    result = await processor.process(frame)
    assert result is None

@pytest.mark.asyncio
async def test_process_unknown_command():
    """Test processing unknown command."""
    processor = CommandProcessor()
    frame = CommandFrame(command="/unknown", metadata={})
    
    result = await processor.process_frame(frame)
    assert isinstance(result, TextFrame)
    assert "Unknown command" in result.text

@pytest.mark.asyncio
async def test_handler_error(command_handler_mock):
    """Test handler error handling."""
    processor = CommandProcessor()
    command_handler_mock.handle.side_effect = RuntimeError("Test error")
    processor.register_handler("/test", command_handler_mock)
    frame = CommandFrame(command="/test", metadata={})
    
    with pytest.raises(RuntimeError):
        await processor.process_frame(frame) 