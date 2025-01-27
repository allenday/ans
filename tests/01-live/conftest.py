"""Test configuration and fixtures."""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from chronicler.storage.coordinator import StorageCoordinator
from chronicler.commands.processor import CommandProcessor
from chronicler.handlers.command import StartCommandHandler, ConfigCommandHandler, StatusCommandHandler
from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from chronicler.pipeline.pipeline import Pipeline
from chronicler.processors.storage_processor import StorageProcessor
from tests.mocks.transports.telegram import MockApplication, MockBot, MockUpdate

@pytest.fixture
def event_loop():
    """Create an event loop for testing."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def storage_path(tmp_path):
    """Create a temporary storage path."""
    return tmp_path / "storage"

@pytest.fixture
def storage_coordinator(storage_path):
    """Create a storage coordinator."""
    return StorageCoordinator(storage_path)

@pytest.fixture
def command_processor(storage_coordinator):
    """Create a command processor with handlers."""
    processor = CommandProcessor(storage_coordinator)
    processor.register_command("/start", StartCommandHandler(storage_coordinator).handle)
    processor.register_command("/config", ConfigCommandHandler(storage_coordinator).handle)
    processor.register_command("/status", StatusCommandHandler(storage_coordinator).handle)
    return processor

@pytest.fixture
def mock_application():
    """Create a mock Telegram application."""
    return MockApplication()

@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot."""
    return MockBot()

@pytest.fixture
def telegram_transport(mock_application):
    """Create a Telegram bot transport with mock application."""
    transport = TelegramBotTransport("test_token")
    transport._app = mock_application
    transport._bot = mock_application.bot
    transport._initialized = True
    return transport

@pytest.fixture
def pipeline(telegram_transport, command_processor, storage_coordinator):
    """Create a pipeline with transport, command processor, and storage."""
    pipeline = Pipeline()
    pipeline.add_processor(telegram_transport)
    pipeline.add_processor(command_processor)
    pipeline.add_processor(StorageProcessor(storage_coordinator))
    telegram_transport.frame_processor = pipeline.process
    return pipeline 