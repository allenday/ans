"""Test command integration with transports."""
import pytest
from chronicler.commands.processor import CommandProcessor
from chronicler.commands.handlers import StartCommandHandler
from chronicler.frames.media import TextFrame

from tests.mocks.storage import storage_mock

@pytest.mark.asyncio
async def test_command_integration(storage_mock):
    """Test command integration with transport."""
    # Setup command processor with storage
    processor = CommandProcessor()
    processor.register_handler("/start", StartCommandHandler(storage_mock))
    
    # Process command
    frame = TextFrame(text="/start", metadata={"chat_id": 123})
    result = await processor.process_frame(frame)
    
    # Verify result
    assert isinstance(result, TextFrame)
    assert "Welcome" in result.text
    storage_mock.init_storage.assert_called_once()
    storage_mock.create_topic.assert_called_once() 