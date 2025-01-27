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