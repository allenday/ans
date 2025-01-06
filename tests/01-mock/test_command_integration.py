"""Integration tests for command handling."""
import pytest
from unittest.mock import Mock, create_autospec
from datetime import datetime

from chronicler.frames import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.processors.command import CommandProcessor
from chronicler.storage import StorageAdapter
from chronicler.storage.interface import Message, User, Topic

@pytest.fixture
def storage_mock():
    """Create a mock storage adapter."""
    storage = create_autospec(StorageAdapter)
    
    # Mock required methods
    storage.init_storage.return_value = storage
    storage.create_topic.return_value = None
    storage.save_message.return_value = "msg_123"
    storage.save_attachment.return_value = None
    storage.sync.return_value = None
    storage.set_github_config.return_value = None
    storage.is_initialized.return_value = True
    
    # Add method call tracking
    storage.init_storage.calls = []
    storage.create_topic.calls = []
    storage.save_message.calls = []
    storage.save_attachment.calls = []
    storage.sync.calls = []
    storage.set_github_config.calls = []
    
    return storage

@pytest.fixture
def processor(storage_mock):
    """Create a command processor."""
    return CommandProcessor(storage_mock)

@pytest.mark.asyncio
async def test_start_command(processor, storage_mock):
    """Test handling /start command."""
    # Setup
    frame = CommandFrame(command="/start", args=[], metadata={"chat_id": 123})
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert isinstance(result, TextFrame)
    assert "Welcome to Chronicler!" in result.text
    storage_mock.init_storage.assert_called_once()
    storage_mock.create_topic.assert_called_once()
    
    # Verify user and topic creation
    user_call = storage_mock.init_storage.call_args[0][0]
    assert isinstance(user_call, User)
    assert user_call.id == "123"
    assert user_call.metadata == {"chat_id": 123}
    
    topic_call = storage_mock.create_topic.call_args[0][0]
    assert isinstance(topic_call, Topic)
    assert topic_call.id == "default"
    assert topic_call.metadata == {"chat_id": 123}

@pytest.mark.asyncio
async def test_config_command_no_args(processor, storage_mock):
    """Test handling /config command with no args."""
    # Setup
    frame = CommandFrame(command="/config", args=[], metadata={"chat_id": 123})
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert isinstance(result, TextFrame)
    assert "Usage: /config" in result.text
    storage_mock.set_github_config.assert_not_called()

@pytest.mark.asyncio
async def test_config_command_with_args(processor, storage_mock):
    """Test handling /config command with args."""
    # Setup
    frame = CommandFrame(
        command="/config",
        args=["owner/repo", "main", "token123"],
        metadata={"chat_id": 123}
    )
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert isinstance(result, TextFrame)
    assert "GitHub configuration updated" in result.text
    storage_mock.set_github_config.assert_called_once_with(
        token="token123",
        repo="owner/repo"
    )

@pytest.mark.asyncio
async def test_status_command(processor, storage_mock):
    """Test handling /status command."""
    # Setup
    frame = CommandFrame(command="/status", args=[], metadata={"chat_id": 123})
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert isinstance(result, TextFrame)
    assert "Chronicler Status" in result.text
    storage_mock.sync.assert_called_once()

@pytest.mark.asyncio
async def test_unknown_command(processor, storage_mock):
    """Test handling unknown command."""
    # Setup
    frame = CommandFrame(command="/unknown", args=[], metadata={"chat_id": 123})
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert isinstance(result, TextFrame)
    assert "Unknown command" in result.text
    storage_mock.save_message.assert_not_called()

@pytest.mark.asyncio
async def test_process_non_command_frame(processor, storage_mock):
    """Test processing a non-command frame."""
    # Setup
    frame = TextFrame(text="Hello", metadata={"chat_id": 123})
    
    # Execute
    result = await processor.process(frame)
    
    # Verify
    assert result is None
    storage_mock.save_message.assert_not_called() 