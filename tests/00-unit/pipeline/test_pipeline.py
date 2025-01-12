"""Tests for pipeline."""
import pytest
from chronicler.pipeline.pipeline import Pipeline
from chronicler.frames.media import TextFrame

from tests.mocks import processor_mock

def test_pipeline_creation():
    """Test pipeline creation."""
    pipeline = Pipeline()
    assert isinstance(pipeline, Pipeline)
    assert len(pipeline.processors) == 0

@pytest.mark.asyncio
async def test_pipeline_processing(processor_mock):
    """Test frame processing through pipeline."""
    pipeline = Pipeline()
    
    # Configure mock processors
    processor1 = processor_mock
    processor1.process.return_value = TextFrame(text="modified1", metadata={})
    
    processor2 = processor_mock
    processor2.process.return_value = TextFrame(text="modified2", metadata={})
    
    # Add processors to pipeline
    pipeline.add_processor(processor1)
    pipeline.add_processor(processor2)
    
    # Process a frame
    frame = TextFrame(text="original", metadata={})
    result = await pipeline.process(frame)
    
    # Verify processors were called in order
    processor1.process.assert_called_once_with(frame)
    processor2.process.assert_called_once()
    assert result.text == "modified2"

@pytest.mark.asyncio
async def test_empty_pipeline():
    """Test processing through empty pipeline."""
    pipeline = Pipeline()
    frame = TextFrame(text="test", metadata={})
    result = await pipeline.process(frame)
    assert result == frame  # Empty pipeline should return original frame 