"""Integration tests for complete message pipeline."""
import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
import os
from datetime import datetime, timezone

from chronicler.logging import get_logger, configure_logging
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.pipeline.pipecat_runner import run_bot
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.filesystem import FileSystemStorage
from chronicler.transports.telegram_factory import TelegramTransportFactory

from tests.mocks.fixtures import mock_session_path, mock_telethon, mock_telegram_bot

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

@pytest_asyncio.fixture
async def storage_processor(storage_coordinator):
    """Create storage processor with real coordinator."""
    processor = StorageProcessor(storage_coordinator)
    return processor

@pytest_asyncio.fixture
async def telegram_transport():
    """Create Telegram transport."""
    if not all(key in os.environ for key in [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH",
        "TELEGRAM_PHONE_NUMBER"
    ]):
        pytest.skip("Telegram credentials not configured")
    
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"]
    )
    await transport.start()
    yield transport
    await transport.stop()

@pytest.mark.asyncio
async def test_complete_message_pipeline(
    storage_coordinator,
    storage_processor,
    telegram_transport,
    tmp_path
):
    """Test complete message pipeline with real components."""
    # Set up test data
    test_image = tmp_path / "test_image.jpg"
    test_image.write_bytes(b"fake image data")
    
    test_frames = [
        TextFrame(
            text="Test message 1",
            metadata={
                "chat_id": "test_chat",
                "message_id": 1,
                "timestamp": datetime.now(timezone.utc)
            }
        ),
        ImageFrame(
            content=test_image.read_bytes(),
            size=(100, 100),
            format="jpeg",
            metadata={
                "chat_id": "test_chat",
                "message_id": 2,
                "timestamp": datetime.now(timezone.utc)
            }
        )
    ]
    
    # Process frames through pipeline
    for frame in test_frames:
        await storage_processor.process(frame)
    
    # Verify storage
    messages = await storage_coordinator.get_messages("test_chat")
    assert len(messages) == 2
    
    # Verify text message
    assert messages[0].content == "Test message 1"
    assert messages[0].metadata["chat_id"] == "test_chat"
    assert messages[0].metadata["message_id"] == 1
    
    # Verify image message
    assert messages[1].metadata["chat_id"] == "test_chat"
    assert messages[1].metadata["message_id"] == 2
    assert len(messages[1].attachments) == 1
    assert messages[1].attachments[0].type == "image/jpeg"

@pytest.mark.asyncio
async def test_pipeline_error_handling(
    storage_coordinator,
    storage_processor,
    telegram_transport,
    tmp_path
):
    """Test pipeline error handling with real components."""
    # Test invalid frame
    invalid_frame = TextFrame(
        text="Test message",
        metadata={
            # Missing required metadata
            "message_id": 1
        }
    )
    
    with pytest.raises(ValueError):
        await storage_processor.process(invalid_frame)
    
    # Test storage errors
    await storage_coordinator.stop()  # Force storage to be unavailable
    
    error_frame = TextFrame(
        text="Test message",
        metadata={
            "chat_id": "test_chat",
            "message_id": 1,
            "timestamp": datetime.now(timezone.utc)
        }
    )
    
    with pytest.raises(Exception):
        await storage_processor.process(error_frame)

@pytest.mark.asyncio
async def test_pipeline_concurrent_processing(
    storage_coordinator,
    storage_processor,
    telegram_transport,
    tmp_path
):
    """Test concurrent message processing through pipeline."""
    # Create multiple test frames
    frames = [
        TextFrame(
            text=f"Test message {i}",
            metadata={
                "chat_id": "test_chat",
                "message_id": i,
                "timestamp": datetime.now(timezone.utc)
            }
        )
        for i in range(10)
    ]
    
    # Process frames concurrently
    tasks = [
        storage_processor.process(frame)
        for frame in frames
    ]
    await asyncio.gather(*tasks)
    
    # Verify all messages were stored
    messages = await storage_coordinator.get_messages("test_chat")
    assert len(messages) == 10
    
    # Verify message order
    message_ids = [msg.metadata["message_id"] for msg in messages]
    assert message_ids == list(range(10))

@pytest.mark.asyncio
async def test_pipeline_performance(
    storage_coordinator,
    storage_processor,
    telegram_transport,
    tmp_path
):
    """Test pipeline performance with real components."""
    import time
    
    # Create test frame
    frame = TextFrame(
        text="Test message",
        metadata={
            "chat_id": "test_chat",
            "message_id": 1,
            "timestamp": datetime.now(timezone.utc)
        }
    )
    
    # Measure processing time
    start_time = time.time()
    await storage_processor.process(frame)
    processing_time = time.time() - start_time
    
    # Assert reasonable processing time (adjust threshold as needed)
    assert processing_time < 1.0, f"Processing took too long: {processing_time:.2f}s"
    
    # Test memory usage
    import psutil
    process = psutil.Process()
    memory_before = process.memory_info().rss
    
    # Process multiple frames
    frames = [
        TextFrame(
            text=f"Test message {i}",
            metadata={
                "chat_id": "test_chat",
                "message_id": i,
                "timestamp": datetime.now(timezone.utc)
            }
        )
        for i in range(100)
    ]
    
    for frame in frames:
        await storage_processor.process(frame)
    
    memory_after = process.memory_info().rss
    memory_increase = (memory_after - memory_before) / 1024 / 1024  # MB
    
    # Assert reasonable memory growth (adjust threshold as needed)
    assert memory_increase < 10, f"Memory usage increased too much: {memory_increase:.2f}MB" 