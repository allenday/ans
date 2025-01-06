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
    frame = TextFrame(text="test message", metadata={})
    result = await transport.send(frame)
    assert result is None  # Send is not implemented for input-only transport

@pytest.mark.asyncio
async def test_transport_process_frame(transport):
    """Test processing a frame through transport."""
    frame = TextFrame(text="test message", metadata={})
    result = await transport.process_frame(frame)
    assert result is None  # Process should ignore frames 