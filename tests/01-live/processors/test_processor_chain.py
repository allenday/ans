"""Integration tests for processor chains."""
import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
import os
from datetime import datetime, timezone

from chronicler.logging import get_logger, configure_logging
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame
from chronicler.processors.base import Processor, ProcessorChain
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.processors.filter_processor import FilterProcessor
from chronicler.processors.transform_processor import TransformProcessor
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.filesystem import FileSystemStorage

from tests.mocks.fixtures import mock_session_path

logger = get_logger(__name__)

@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for all tests."""
    configure_logging(level='DEBUG')

@pytest_asyncio.fixture
async def storage_path(tmp_path):
    """Create temporary storage path."""
    storage_dir = tmp_path / "test_storage"
    storage_dir.mkdir(exist_ok=True)
    return storage_dir

@pytest_asyncio.fixture
async def storage_coordinator(storage_path):
    """Create storage coordinator with real components."""
    git_storage = GitStorageAdapter(storage_path)
    file_storage = FileSystemStorage(storage_path)
    coordinator = StorageCoordinator(git_storage, file_storage)
    await coordinator.init()
    return coordinator

class LoggingProcessor(Processor):
    """Processor that logs all frames passing through."""
    
    def __init__(self):
        self.processed_frames = []
    
    async def process(self, frame):
        """Log frame and pass through."""
        self.processed_frames.append(frame)
        return frame

class TransformingProcessor(Processor):
    """Processor that transforms frames."""
    
    async def process(self, frame):
        """Add transformation metadata to frame."""
        if isinstance(frame, TextFrame):
            frame.metadata["transformed"] = True
            frame.text = frame.text.upper()
        return frame

class FilteringProcessor(Processor):
    """Processor that filters frames."""
    
    async def process(self, frame):
        """Filter out frames based on criteria."""
        if isinstance(frame, ImageFrame):
            return None  # Filter out image frames
        return frame

@pytest.mark.asyncio
async def test_processor_chain_basic(storage_coordinator):
    """Test basic processor chain functionality."""
    # Create processors
    logging_proc = LoggingProcessor()
    transform_proc = TransformingProcessor()
    storage_proc = StorageProcessor(storage_coordinator)
    
    # Create processor chain
    chain = ProcessorChain([
        logging_proc,
        transform_proc,
        storage_proc
    ])
    
    # Create test frame
    frame = TextFrame(
        text="test message",
        metadata={
            "chat_id": "test_chat",
            "message_id": 1,
            "timestamp": datetime.now(timezone.utc)
        }
    )
    
    # Process frame through chain
    result = await chain.process(frame)
    
    # Verify frame was logged
    assert len(logging_proc.processed_frames) == 1
    assert logging_proc.processed_frames[0] is frame
    
    # Verify frame was transformed
    assert result.text == "TEST MESSAGE"
    assert result.metadata["transformed"] is True
    
    # Verify frame was stored
    messages = await storage_coordinator.get_messages("test_chat")
    assert len(messages) == 1
    assert messages[0].content == "TEST MESSAGE"

@pytest.mark.asyncio
async def test_processor_chain_filtering(storage_coordinator):
    """Test processor chain with filtering."""
    # Create processors
    logging_proc = LoggingProcessor()
    filter_proc = FilteringProcessor()
    storage_proc = StorageProcessor(storage_coordinator)
    
    # Create processor chain
    chain = ProcessorChain([
        logging_proc,
        filter_proc,
        storage_proc
    ])
    
    # Create test frames
    text_frame = TextFrame(
        text="test message",
        metadata={
            "chat_id": "test_chat",
            "message_id": 1,
            "timestamp": datetime.now(timezone.utc)
        }
    )
    
    image_frame = ImageFrame(
        content=b"fake image data",
        size=(100, 100),
        format="jpeg",
        metadata={
            "chat_id": "test_chat",
            "message_id": 2,
            "timestamp": datetime.now(timezone.utc)
        }
    )
    
    # Process frames
    await chain.process(text_frame)
    await chain.process(image_frame)
    
    # Verify logging
    assert len(logging_proc.processed_frames) == 2
    
    # Verify storage (image should be filtered out)
    messages = await storage_coordinator.get_messages("test_chat")
    assert len(messages) == 1
    assert messages[0].content == "test message"

@pytest.mark.asyncio
async def test_processor_chain_error_handling(storage_coordinator):
    """Test processor chain error handling."""
    class ErrorProcessor(Processor):
        async def process(self, frame):
            raise ValueError("Test error")
    
    # Create processor chain with error handler
    logging_proc = LoggingProcessor()
    error_proc = ErrorProcessor()
    
    chain = ProcessorChain([
        logging_proc,
        error_proc
    ])
    
    # Create test frame
    frame = TextFrame(
        text="test message",
        metadata={
            "chat_id": "test_chat",
            "message_id": 1,
            "timestamp": datetime.now(timezone.utc)
        }
    )
    
    # Process frame and expect error
    with pytest.raises(ValueError):
        await chain.process(frame)
    
    # Verify frame was logged before error
    assert len(logging_proc.processed_frames) == 1

@pytest.mark.asyncio
async def test_processor_chain_concurrent(storage_coordinator):
    """Test concurrent processing through chain."""
    # Create processors
    logging_proc = LoggingProcessor()
    transform_proc = TransformingProcessor()
    storage_proc = StorageProcessor(storage_coordinator)
    
    # Create processor chain
    chain = ProcessorChain([
        logging_proc,
        transform_proc,
        storage_proc
    ])
    
    # Create multiple frames
    frames = [
        TextFrame(
            text=f"test message {i}",
            metadata={
                "chat_id": "test_chat",
                "message_id": i,
                "timestamp": datetime.now(timezone.utc)
            }
        )
        for i in range(10)
    ]
    
    # Process frames concurrently
    tasks = [chain.process(frame) for frame in frames]
    await asyncio.gather(*tasks)
    
    # Verify all frames were processed
    assert len(logging_proc.processed_frames) == 10
    
    # Verify storage
    messages = await storage_coordinator.get_messages("test_chat")
    assert len(messages) == 10
    
    # Verify message order
    message_ids = [msg.metadata["message_id"] for msg in messages]
    assert message_ids == list(range(10))

@pytest.mark.asyncio
async def test_processor_chain_performance(storage_coordinator):
    """Test processor chain performance."""
    import time
    
    # Create processor chain
    chain = ProcessorChain([
        LoggingProcessor(),
        TransformingProcessor(),
        StorageProcessor(storage_coordinator)
    ])
    
    # Create test frame
    frame = TextFrame(
        text="test message",
        metadata={
            "chat_id": "test_chat",
            "message_id": 1,
            "timestamp": datetime.now(timezone.utc)
        }
    )
    
    # Measure processing time
    start_time = time.time()
    await chain.process(frame)
    processing_time = time.time() - start_time
    
    # Assert reasonable processing time
    assert processing_time < 1.0, f"Processing took too long: {processing_time:.2f}s"
    
    # Test memory usage with many frames
    import psutil
    process = psutil.Process()
    memory_before = process.memory_info().rss
    
    # Process multiple frames
    frames = [
        TextFrame(
            text=f"test message {i}",
            metadata={
                "chat_id": "test_chat",
                "message_id": i,
                "timestamp": datetime.now(timezone.utc)
            }
        )
        for i in range(100)
    ]
    
    for frame in frames:
        await chain.process(frame)
    
    memory_after = process.memory_info().rss
    memory_increase = (memory_after - memory_before) / 1024 / 1024  # MB
    
    # Assert reasonable memory growth
    assert memory_increase < 10, f"Memory usage increased too much: {memory_increase:.2f}MB" 