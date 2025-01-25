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

@pytest.mark.asyncio
async def test_sequential_frame_transformation(processor_mock):
    """Test that each processor can transform the frame and pass it to the next processor."""
    pipeline = Pipeline()
    
    # Create processors that modify the frame content
    processor1 = processor_mock()
    processor1.process.return_value = TextFrame(content="modified by p1", metadata={})
    
    processor2 = processor_mock()
    processor2.process.return_value = TextFrame(content="modified by p2", metadata={})
    
    pipeline.add_processor(processor1)
    pipeline.add_processor(processor2)

    frame = TextFrame(content="original", metadata={})
    result = await pipeline.process(frame)

    # Verify processor1 got original frame
    processor1.process.assert_called_once_with(frame)
    
    # Verify processor2 got frame from processor1
    processor2.process.assert_called_once()
    p2_input = processor2.process.call_args[0][0]
    assert isinstance(p2_input, TextFrame)
    assert p2_input.content == "modified by p1"
    
    # Verify final result
    assert isinstance(result, TextFrame)
    assert result.content == "modified by p2"

@pytest.mark.asyncio
async def test_processor_error_logging(processor_mock, caplog):
    """Test that processor errors are properly logged."""
    pipeline = Pipeline()
    processor = processor_mock()
    error_msg = "Test processing error"
    processor.process.side_effect = RuntimeError(error_msg)
    pipeline.add_processor(processor)

    frame = TextFrame(content="test", metadata={})
    with pytest.raises(RuntimeError):
        await pipeline.process(frame)

    assert "PIPELINE - Error in processor" in caplog.text
    assert error_msg in caplog.text
    assert "RuntimeError" in caplog.text

@pytest.mark.asyncio
async def test_processor_debug_logging(processor_mock, caplog):
    """Test debug level logging during frame processing."""
    pipeline = Pipeline()
    processor = processor_mock()
    processor.process.return_value = TextFrame(content="modified", metadata={})
    pipeline.add_processor(processor)

    frame = TextFrame(content="test", metadata={})
    with caplog.at_level('DEBUG'):
        await pipeline.process(frame)

    # Check debug logs for processor execution
    assert "PIPELINE - Running processor 1/1" in caplog.text
    assert "PIPELINE - Processor" in caplog.text
    assert "transformed frame to TextFrame" in caplog.text 