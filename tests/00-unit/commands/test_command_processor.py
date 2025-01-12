"""Tests for command processor."""
import pytest
from unittest.mock import Mock, AsyncMock, create_autospec
from chronicler.commands.processor import CommandProcessor
from chronicler.commands.frames import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.commands.handlers import CommandHandler
from chronicler.storage import StorageAdapter

@pytest.fixture
def storage_mock():
    """Create a mock storage adapter."""
    storage = create_autospec(StorageAdapter)
    storage.init_storage.return_value = storage
    storage.create_topic.return_value = None
    storage.save_message = AsyncMock(return_value="msg_123")
    storage.save_attachment = AsyncMock(return_value=None)
    storage.sync = AsyncMock(return_value=None)
    storage.set_github_config = AsyncMock(return_value=None)
    storage.is_initialized.return_value = True
    return storage

@pytest.mark.asyncio
async def test_command_processor_init(storage_mock):
    """Test command processor initialization."""
    processor = CommandProcessor()
    assert len(processor._handlers) == 0  # No default handlers

@pytest.mark.asyncio
async def test_register_handler(storage_mock):
    """Test handler registration."""
    processor = CommandProcessor()
    handler = AsyncMock(spec=CommandHandler)
    
    processor.register_handler("/test", handler)
    assert processor._handlers["/test"] == handler

@pytest.mark.asyncio
async def test_register_handler_duplicate(storage_mock):
    """Test registering duplicate handler."""
    processor = CommandProcessor()
    handler1 = AsyncMock(spec=CommandHandler)
    handler2 = AsyncMock(spec=CommandHandler)
    
    processor.register_handler("/test", handler1)
    processor.register_handler("/test", handler2)
    assert processor._handlers["/test"] == handler2

@pytest.mark.asyncio
async def test_register_handler_validation(storage_mock):
    """Test handler registration validation."""
    processor = CommandProcessor()
    handler = AsyncMock()  # Not a CommandHandler
    
    with pytest.raises(ValueError):
        processor.register_handler("/test", handler)

@pytest.mark.asyncio
async def test_process_non_command_frame(storage_mock):
    """Test processing non-command frame."""
    processor = CommandProcessor()
    frame = TextFrame(content="test", metadata={})
    
    result = await processor.process_frame(frame)
    assert result is None

@pytest.mark.asyncio
async def test_process_unknown_command(storage_mock):
    """Test processing unknown command."""
    processor = CommandProcessor()
    frame = CommandFrame(command="/unknown", metadata={})
    
    result = await processor.process_frame(frame)
    assert isinstance(result, TextFrame)
    assert "Unknown command" in result.content

@pytest.mark.asyncio
async def test_handler_error(storage_mock):
    """Test handler error handling."""
    processor = CommandProcessor()
    handler = AsyncMock(spec=CommandHandler)
    handler.handle.side_effect = RuntimeError("Test error")
    processor.register_handler("/test", handler)
    frame = CommandFrame(command="/test", metadata={})
    
    with pytest.raises(RuntimeError):
        await processor.process_frame(frame)
        await handler.handle.return_value 