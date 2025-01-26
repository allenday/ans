"""Test cases for command integration."""

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
    processor = CommandProcessor()
    start_handler = StartCommandHandler(coordinator=coordinator_mock)
    config_handler = ConfigCommandHandler(coordinator=coordinator_mock)
    status_handler = StatusCommandHandler(coordinator=coordinator_mock)

    processor.register_handler(command="/start", handler=start_handler)
    processor.register_handler(command="/config", handler=config_handler)
    processor.register_handler(command="/status", handler=status_handler)

    # Mock coordinator behavior
    coordinator_mock.is_initialized.side_effect = [False, True, True]
    coordinator_mock.init_storage = AsyncMock()
    coordinator_mock.create_topic = AsyncMock()
    coordinator_mock.set_github_config = AsyncMock()
    coordinator_mock.sync = AsyncMock()

    # Test /start command
    start_frame = command_frame_factory(command="/start")
    result = await processor.process(start_frame)
    assert isinstance(result, TextFrame)
    assert "initialized" in result.content.lower()
    coordinator_mock.init_storage.assert_awaited_once()
    coordinator_mock.create_topic.assert_awaited_once()

    # Test /config command
    config_frame = command_frame_factory(
        command="/config",
        args=["user/repo", "ghp_token123"]
    )
    result = await processor.process(config_frame)
    assert isinstance(result, TextFrame)
    assert "configuration" in result.content.lower()
    coordinator_mock.set_github_config.assert_awaited_once_with(
        token="ghp_token123",
        repo="user/repo"
    )

    # Test /status command
    status_frame = command_frame_factory(command="/status")
    result = await processor.process(status_frame)
    assert isinstance(result, TextFrame)
    assert "status" in result.content.lower()
    assert coordinator_mock.sync.await_count == 2  # Called by both config and status handlers 