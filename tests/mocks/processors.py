"""Mock implementations for processors."""
import pytest
from unittest.mock import AsyncMock, create_autospec

from chronicler.processors.base import BaseProcessor
from chronicler.frames.media import TextFrame

@pytest.fixture
def processor_mock():
    """Create a mock processor factory."""
    def create_mock():
        processor = create_autospec(BaseProcessor)
        processor.process = AsyncMock(return_value=TextFrame(text="mock_processed", metadata={}))
        return processor
    return create_mock 