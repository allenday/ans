"""Mock implementations for command handlers."""
import pytest
from unittest.mock import AsyncMock, create_autospec

from chronicler.commands.handlers import CommandHandler
from chronicler.frames.media import TextFrame

@pytest.fixture
def command_handler_mock():
    """Create a mock command handler."""
    handler = create_autospec(CommandHandler)
    handler.handle = AsyncMock(return_value=TextFrame(text="mock_handled", metadata={}))
    return handler 