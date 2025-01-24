"""Mock classes and fixtures for processor tests."""
import pytest
from unittest.mock import AsyncMock, Mock
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.handlers.command import CommandHandler
from chronicler.storage.coordinator import StorageCoordinator

class TestCommandHandler(CommandHandler):
    """Test command handler implementation."""
    def __init__(self):
        """Initialize test command handler."""
        super().__init__()
        
    async def handle(self, frame: CommandFrame):
        """Handle test command."""
        return TextFrame(content="test response", metadata=frame.metadata)

@pytest.fixture
def storage():
    """Create a mock storage coordinator."""
    mock = Mock(spec=StorageCoordinator)
    mock.is_initialized = AsyncMock()
    mock.get_topics = AsyncMock()
    mock.get_messages = AsyncMock()
    mock.init_storage = AsyncMock()
    mock.create_topic = AsyncMock()
    mock.topic_exists.return_value = False
    return mock

@pytest.fixture
def metadata():
    """Create test metadata."""
    return {
        'chat_id': 123,
        'thread_id': 456,
        'message_id': 789
    }

@pytest.fixture
def command_processor(storage):
    """Create a command processor instance."""
    from chronicler.processors.command import CommandProcessor
    return CommandProcessor(storage)

@pytest.fixture
def storage_processor(storage):
    """Create a storage processor instance."""
    from chronicler.processors.storage_processor import StorageProcessor
    return StorageProcessor(storage)

@pytest.fixture
def processor_mock():
    """Create a mock processor factory."""
    def create_mock():
        processor = create_autospec(BaseProcessor)
        processor.process = AsyncMock(return_value=TextFrame(content="mock_processed", metadata={}))
        return processor
    return create_mock 