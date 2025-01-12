"""Live tests for TelegramTransport."""
import pytest
import pytest_asyncio
import os
from unittest.mock import AsyncMock
from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame
from chronicler.transports.telegram_transport import TelegramTransport

@pytest.fixture
def token():
    """Get Telegram bot token from environment."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        pytest.skip("TELEGRAM_BOT_TOKEN not set")
    return token

@pytest_asyncio.fixture
async def transport(token):
    """Create a TelegramTransport instance."""
    transport = TelegramTransport(token)
    try:
        yield transport
    finally:
        await transport.stop()

@pytest.mark.asyncio
async def test_transport_initialization(transport):
    """Test initializing the transport."""
    assert transport.token is not None
    assert transport.app is not None
    assert not transport.app.running

@pytest.mark.asyncio
async def test_transport_start_stop(transport):
    """Test starting and stopping the transport."""
    await transport.start()
    assert transport.app.running
    await transport.stop()
    assert not transport.app.running

@pytest.mark.asyncio
async def test_transport_send_frame(transport):
    """Test sending a frame through transport."""
    # Start transport
    await transport.start()
    
    # Create frame with required metadata
    frame = TextFrame(
        content="test message",
        metadata={
            'chat_id': os.getenv('TELEGRAM_TEST_GROUP_ID'),
            'thread_id': os.getenv('TELEGRAM_TEST_TOPIC_ID')
        }
    )
    
    # Send frame
    result = await transport.send(frame)
    
    # Verify result
    assert result is not None
    assert isinstance(result, TextFrame)
    assert result.content == frame.content
    assert result.metadata['direction'] == 'outgoing'
    assert result.metadata['is_from_bot'] is True
    
    # Stop transport
    await transport.stop()

@pytest.mark.asyncio
async def test_transport_handle_message(transport):
    """Test handling an incoming message."""
    # Start transport
    await transport.start()
    
    # Create mock update
    update = AsyncMock()
    update.message.text = "test message"
    update.message.message_id = 123
    update.message.chat.id = -1001234567890
    update.message.chat.title = "Test Group"
    update.message.from_user.id = 987654321
    update.message.from_user.username = "test_user"
    update.message.from_user.is_bot = False
    
    # Create frame receiver
    received_frames = []
    async def frame_receiver(frame):
        received_frames.append(frame)
    transport.push_frame = frame_receiver
    
    # Handle message
    await transport._handle_message(update, None)
    
    # Verify frame was created and pushed
    assert len(received_frames) == 1
    frame = received_frames[0]
    assert isinstance(frame, TextFrame)
    assert frame.content == "test message"
    assert frame.metadata['direction'] == 'incoming'
    assert frame.metadata['is_from_bot'] is False
    
    # Stop transport
    await transport.stop() 