"""Unit tests for Pipeline class."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from chronicler.pipeline import Pipeline, BaseProcessor, Frame

class MockProcessor(BaseProcessor):
    """Mock processor for testing."""
    async def process_frame(self, frame: Frame):
        await self.push_frame(frame)

@pytest.mark.asyncio
async def test_pipeline_creation():
    """Test creating a pipeline with processors."""
    processors = [MockProcessor(), MockProcessor()]
    pipeline = Pipeline(processors)
    assert len(pipeline.processors) == 2
    assert pipeline.processors[0].next_processor == pipeline.processors[1]

@pytest.mark.asyncio
async def test_pipeline_processing():
    """Test processing a frame through the pipeline."""
    # Create mock processors
    processor1 = MockProcessor()
    processor2 = MockProcessor()
    
    # Create spy on process_frame methods
    processor1.process_frame = AsyncMock(wraps=processor1.process_frame)
    processor2.process_frame = AsyncMock(wraps=processor2.process_frame)
    
    # Create pipeline
    pipeline = Pipeline([processor1, processor2])
    
    # Create test frame
    frame = MagicMock(spec=Frame)
    
    # Process frame
    await pipeline.process_frame(frame)
    
    # Verify both processors were called
    processor1.process_frame.assert_called_once_with(frame)
    processor2.process_frame.assert_called_once_with(frame)

@pytest.mark.asyncio
async def test_empty_pipeline():
    """Test processing a frame through an empty pipeline."""
    pipeline = Pipeline([])
    frame = MagicMock(spec=Frame)
    await pipeline.process_frame(frame)  # Should not raise any errors 