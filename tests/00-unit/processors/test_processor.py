"""Tests for frame processors."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from chronicler.frames.media import TextFrame
from chronicler.exceptions import TransportError
from chronicler.processors.base import BaseProcessor
from unittest.mock import call

class TestProcessor(BaseProcessor):
    """Test processor implementation."""
    async def process(self, frame):
        return frame

@pytest.mark.asyncio
async def test_process_frame_without_processor():
    """Test processing frame without frame processor."""
    processor = TestProcessor()
    frame = TextFrame(content="test", metadata={"chat_id": 123})
    
    result = await processor.process(frame)
    assert result == frame  # Should return unmodified frame

@pytest.mark.asyncio
async def test_process_frame_with_transformation():
    """Test processing frame with content transformation."""
    class UppercaseProcessor(TestProcessor):
        async def process(self, frame):
            frame.content = frame.content.upper()
            return frame
    
    processor = UppercaseProcessor()
    frame = TextFrame(content="test", metadata={"chat_id": 123})
    
    result = await processor.process(frame)
    assert result.content == "TEST"
    assert result.metadata == frame.metadata  # Metadata unchanged

@pytest.mark.asyncio
async def test_processor_returns_none():
    """Test handling when processor returns None."""
    class FilterProcessor(TestProcessor):
        async def process(self, frame):
            if frame.content == "filter_me":
                return None
            return frame
    
    processor = FilterProcessor()
    
    # Frame that should be filtered
    frame1 = TextFrame(content="filter_me", metadata={"chat_id": 123})
    result1 = await processor.process(frame1)
    assert result1 is None
    
    # Frame that should pass through
    frame2 = TextFrame(content="keep_me", metadata={"chat_id": 123})
    result2 = await processor.process(frame2)
    assert result2 == frame2

@pytest.mark.asyncio
async def test_processor_modifies_metadata():
    """Test that processor can modify frame metadata."""
    class MetadataProcessor(TestProcessor):
        async def process(self, frame):
            frame.metadata["processed"] = True
            frame.metadata["timestamp"] = "test_time"
            return frame
    
    processor = MetadataProcessor()
    frame = TextFrame(
        content="test message",
        metadata={"chat_id": 123}
    )
    
    result = await processor.process(frame)
    
    # Verify metadata was added
    assert result.metadata["processed"] is True
    assert result.metadata["timestamp"] == "test_time"
    assert result.metadata["chat_id"] == 123  # Original metadata preserved

@pytest.mark.asyncio
async def test_processor_error_handling():
    """Test error handling in processor."""
    class ErrorProcessor(TestProcessor):
        async def process(self, frame):
            raise TransportError("Process error")
    
    processor = ErrorProcessor()
    frame = TextFrame(
        content="test message",
        metadata={"chat_id": 123}
    )
    
    with pytest.raises(TransportError, match="Process error"):
        await processor.process(frame)

@pytest.mark.asyncio
async def test_processor_chain():
    """Test chaining multiple processors."""
    class UppercaseProcessor(TestProcessor):
        async def process(self, frame):
            frame.content = frame.content.upper()
            return frame
            
    class MetadataProcessor(TestProcessor):
        async def process(self, frame):
            frame.metadata["processed"] = True
            return frame
    
    # Chain processors
    processor1 = UppercaseProcessor()
    processor2 = MetadataProcessor()
    
    frame = TextFrame(content="test", metadata={"chat_id": 123})
    
    # Process through chain
    result = await processor1.process(frame)
    result = await processor2.process(result)
    
    # Verify both processors affected the frame
    assert result.content == "TEST"
    assert result.metadata["processed"] is True
    assert result.metadata["chat_id"] == 123 

"""Unit tests for base processor implementations."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from chronicler.processors.base import BaseProcessor, ProcessorChain
from chronicler.frames import Frame
from dataclasses import dataclass

@dataclass
class TestFrame(Frame):
    """Test frame implementation."""
    pass

class TestProcessor(BaseProcessor):
    """Test processor implementation."""
    async def process(self, frame: Frame):
        return frame

class NullProcessor(BaseProcessor):
    """Processor that returns None."""
    async def process(self, frame: Frame):
        return None

@pytest.mark.asyncio
async def test_base_processor_logging():
    """Test that BaseProcessor initialization is logged."""
    with patch('chronicler.processors.base.logger') as mock_logger:
        processor = TestProcessor()
        mock_logger.debug.assert_called_once()
        assert "Initialized BaseProcessor" in mock_logger.debug.call_args[0][0]

@pytest.mark.asyncio
async def test_processor_chain_empty():
    """Test ProcessorChain with no processors."""
    chain = ProcessorChain()
    frame = TestFrame()
    result = await chain.process(frame)
    assert result == frame

@pytest.mark.asyncio
async def test_processor_chain_single():
    """Test ProcessorChain with a single processor."""
    processor = TestProcessor()
    chain = ProcessorChain([processor])
    frame = TestFrame()
    result = await chain.process(frame)
    assert result == frame

@pytest.mark.asyncio
async def test_processor_chain_multiple():
    """Test ProcessorChain with multiple processors."""
    processors = [TestProcessor(), TestProcessor()]
    chain = ProcessorChain(processors)
    frame = TestFrame()
    result = await chain.process(frame)
    assert result == frame

@pytest.mark.asyncio
async def test_processor_chain_null_processor():
    """Test ProcessorChain with a processor that returns None."""
    processors = [TestProcessor(), NullProcessor(), TestProcessor()]
    chain = ProcessorChain(processors)
    frame = TestFrame()
    result = await chain.process(frame)
    assert result is None

@pytest.mark.asyncio
async def test_processor_chain_add_processor():
    """Test adding a processor to the chain."""
    chain = ProcessorChain()
    with patch('chronicler.processors.base.logger') as mock_logger:
        chain.add_processor(TestProcessor())
        assert mock_logger.debug.call_count == 2
        mock_logger.debug.assert_has_calls([
            call('PROC - Initialized BaseProcessor'),
            call('PROC - Added processor TestProcessor to chain')
        ])

@pytest.mark.asyncio
async def test_processor_chain_logging():
    """Test ProcessorChain initialization logging."""
    processors = [TestProcessor(), TestProcessor()]
    with patch('chronicler.processors.base.logger') as mock_logger:
        chain = ProcessorChain(processors)
        mock_logger.debug.assert_called()
        log_msg = mock_logger.debug.call_args[0][0]
        assert "Initialized ProcessorChain" in log_msg
        assert "2 processors" in log_msg 