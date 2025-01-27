"""Test command integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.handlers.command import StartCommandHandler, ConfigCommandHandler, StatusCommandHandler
from chronicler.commands.processor import CommandProcessor
from tests.mocks.commands import command_frame_factory, coordinator_mock, TEST_METADATA

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

@pytest.mark.asyncio
async def test_command_flow(coordinator_mock, command_frame_factory):
    """Test the complete command flow from start to status."""
    # Setup command processor with handlers
    processor = CommandProcessor(coordinator=coordinator_mock)
    start_handler = StartCommandHandler(coordinator=coordinator_mock)
    config_handler = ConfigCommandHandler(coordinator=coordinator_mock)
    status_handler = StatusCommandHandler(coordinator=coordinator_mock)
    
    # Configure mock behavior
    coordinator_mock.is_initialized.return_value = False  # Initially not initialized
    coordinator_mock.initialize.return_value = None  # Initialize succeeds
    coordinator_mock.create_default_topic.return_value = None  # Create topic succeeds
    coordinator_mock.configure_github.return_value = None  # Configure GitHub succeeds
    coordinator_mock.sync.return_value = None  # Sync succeeds
    
    # Register handlers
    processor.register_command("/start", start_handler.handle)
    processor.register_command("/config", config_handler.handle)
    processor.register_command("/status", status_handler.handle)
    
    # Test /start command
    start_frame = command_frame_factory("/start")
    response = await processor.process(start_frame)
    assert response.content == "Storage initialized successfully! You can now configure your GitHub repository with /config."
    
    # Update mock state after initialization
    coordinator_mock.is_initialized.return_value = True
    
    # Test /config command
    config_frame = command_frame_factory("/config", args=["username/repo", "ghp_token"])
    response = await processor.process(config_frame)
    assert response.content == "GitHub configuration updated!\n\nI'll now archive your messages to:\nhttps://github.com/username/repo\n\nYou can check the current status with /status"
    
    # Test /status command
    status_frame = command_frame_factory("/status")
    response = await processor.process(status_frame)
    assert response.content == "Chronicler Status:\n- Storage: Initialized\n- GitHub: Connected\n- Last sync: Success"

@pytest.mark.asyncio
async def test_command_direct_response_flow(coordinator_mock, command_frame_factory):
    """Test the direct response flow without queueing and command context management."""
    # Setup command processor with handlers
    processor = CommandProcessor(coordinator=coordinator_mock)
    
    # Create a stateful command that requires multiple steps
    async def config_handler(frame):
        chat_id = frame.metadata.get("chat_id")
        if isinstance(frame, CommandFrame):
            return TextFrame(content="Please provide repository name", metadata=frame.metadata)
        else:
            # Process the repository name
            repo_name = frame.content
            await coordinator_mock.set_github_config(repo_name, "dummy_token")
            processor.complete(chat_id)  # Explicitly complete command
            return TextFrame(content=f"Repository set to: {repo_name}", metadata=frame.metadata)
    
    processor.register_command("/config", config_handler)
    
    # Test initial command
    config_frame = command_frame_factory("/config")
    response = await processor.process(config_frame)
    assert response.content == "Please provide repository name"
    assert processor.get_active_command(123) == "/config"  # Command context is maintained
    
    # Test providing repository name
    text_frame = TextFrame(content="test/repo", metadata={"chat_id": 123})
    response = await processor.process(text_frame)
    assert response.content == "Repository set to: test/repo"
    assert processor.get_active_command(123) is None  # Command context is cleared
    
    # Verify coordinator was called
    coordinator_mock.set_github_config.assert_awaited_once_with("test/repo", "dummy_token")

@pytest.mark.asyncio
async def test_command_interruption_flow(coordinator_mock, command_frame_factory):
    """Test command interruption and context clearing in the pipeline."""
    processor = CommandProcessor(coordinator=coordinator_mock)
    
    # Create two command handlers
    async def config_handler(frame):
        if isinstance(frame, CommandFrame):
            return TextFrame(content="Please provide repository name", metadata=frame.metadata)
        processor.complete(frame.metadata["chat_id"])  # Explicitly complete command
        return TextFrame(content=f"Config received: {frame.content}", metadata=frame.metadata)
        
    async def status_handler(frame):
        processor.complete(frame.metadata["chat_id"])  # Explicitly complete command
        return TextFrame(content="Status: OK", metadata=frame.metadata)
    
    processor.register_command("/config", config_handler)
    processor.register_command("/status", status_handler)
    
    # Start config command
    config_frame = command_frame_factory("/config")
    response = await processor.process(config_frame)
    assert response.content == "Please provide repository name"
    assert processor.get_active_command(123) == "/config"
    
    # Interrupt with status command
    status_frame = command_frame_factory("/status")
    response = await processor.process(status_frame)
    assert response.content == "Status: OK"
    assert processor.get_active_command(123) is None  # Previous command context is cleared
    
    # Verify original command context is cleared by trying to send input
    text_frame = TextFrame(content="test/repo", metadata={"chat_id": 123})
    response = await processor.process(text_frame)
    assert response is None  # No active command to handle the input 