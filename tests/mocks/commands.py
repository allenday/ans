"""Mock implementations for command handlers."""
import pytest
from unittest.mock import AsyncMock, create_autospec

from chronicler.commands.handlers import CommandHandler
from chronicler.frames.media import TextFrame
from chronicler.frames.command import CommandFrame
from chronicler.storage.coordinator import StorageCoordinator

# Test metadata used across command tests
TEST_METADATA = {"chat_id": 123}

@pytest.fixture
def command_handler_mock():
    """Create a mock command handler."""
    handler = create_autospec(CommandHandler)
    handler.handle = AsyncMock(return_value=TextFrame(content="mock_handled", metadata={}))
    return handler

@pytest.fixture
def coordinator_mock():
    """Create a mock storage coordinator."""
    mock = AsyncMock()
    mock.is_initialized = AsyncMock()
    mock.init_storage = AsyncMock()
    mock.create_topic = AsyncMock()
    mock.set_github_config = AsyncMock()
    mock.sync = AsyncMock()
    return mock

@pytest.fixture
def start_handler_mock(coordinator_mock):
    """Create a mock StartCommandHandler."""
    handler = create_autospec(CommandHandler)
    handler.command = "/start"
    handler.handle = AsyncMock(return_value=TextFrame(
        content="Storage initialized successfully!",
        metadata=TEST_METADATA
    ))
    return handler

@pytest.fixture
def config_handler_mock(coordinator_mock):
    """Create a mock ConfigCommandHandler."""
    handler = create_autospec(CommandHandler)
    handler.command = "/config"
    handler.handle = AsyncMock(return_value=TextFrame(
        content="GitHub configuration updated!",
        metadata=TEST_METADATA
    ))
    return handler

@pytest.fixture
def status_handler_mock(coordinator_mock):
    """Create a mock StatusCommandHandler."""
    handler = create_autospec(CommandHandler)
    handler.command = "/status"
    handler.handle = AsyncMock(return_value=TextFrame(
        content="Current status: initialized and configured",
        metadata=TEST_METADATA
    ))
    return handler

@pytest.fixture
def command_frame_factory():
    """Create a CommandFrame with the given command and optional args."""
    def _create_frame(command: str, args: list[str] = None):
        return CommandFrame(
            command=command,
            args=args or [],
            metadata=TEST_METADATA
        )
    return _create_frame 