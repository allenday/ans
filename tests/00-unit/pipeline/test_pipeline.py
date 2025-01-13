"""Tests for pipeline."""
import pytest
from unittest.mock import create_autospec, AsyncMock
from chronicler.frames.media import TextFrame
from chronicler.pipeline.pipeline import Pipeline
from chronicler.processors.base import BaseProcessor

@pytest.fixture
def processor_mock():
    """Create a mock processor factory."""
    def create_mock():
        processor = create_autospec(BaseProcessor)
        processor.process = AsyncMock(return_value=TextFrame(content="mock_processed", metadata={}))
        return processor
    return create_mock

@pytest.mark.asyncio
async def test_pipeline_creation():
    """Test creating a pipeline instance."""
    pipeline = Pipeline()
    assert len(pipeline.processors) == 0

@pytest.mark.asyncio
async def test_pipeline_processing(processor_mock):
    """Test processing a frame through multiple processors."""
    pipeline = Pipeline()
    processor1 = processor_mock()
    processor2 = processor_mock()
    pipeline.add_processor(processor1)
    pipeline.add_processor(processor2)

    frame = TextFrame(content="test", metadata={})
    result = await pipeline.process(frame)

    processor1.process.assert_called_once_with(frame)
    processor2.process.assert_called_once()
    assert isinstance(result, TextFrame)

@pytest.mark.asyncio
async def test_empty_pipeline():
    """Test processing through an empty pipeline."""
    pipeline = Pipeline()
    frame = TextFrame(content="test", metadata={})
    result = await pipeline.process(frame)
    assert result == frame

@pytest.mark.asyncio
async def test_invalid_processor_type():
    """Test adding an invalid processor type."""
    pipeline = Pipeline()
    with pytest.raises(TypeError):
        pipeline.add_processor("not a processor")

@pytest.mark.asyncio
async def test_processor_error(processor_mock):
    """Test error handling when a processor raises an exception."""
    pipeline = Pipeline()
    processor = processor_mock()
    processor.process.side_effect = RuntimeError("Test error")
    pipeline.add_processor(processor)

    frame = TextFrame(content="test", metadata={})
    with pytest.raises(RuntimeError):
        await pipeline.process(frame)

@pytest.mark.asyncio
async def test_processor_returns_none(processor_mock):
    """Test handling when a processor returns None."""
    pipeline = Pipeline()
    processor = processor_mock()
    processor.process.return_value = None
    pipeline.add_processor(processor)

    frame = TextFrame(content="test", metadata={})
    result = await pipeline.process(frame)
    assert result == frame  # Should return original frame if processor returns None

@pytest.mark.asyncio
async def test_pipeline_logging(processor_mock, caplog):
    """Test that pipeline operations are properly logged."""
    pipeline = Pipeline()
    processor = processor_mock()
    pipeline.add_processor(processor)

    frame = TextFrame(content="test", metadata={})
    await pipeline.process(frame)

    assert "PIPELINE - Processing frame of type TextFrame" in caplog.text
    assert "PIPELINE - Frame processing complete" in caplog.text 