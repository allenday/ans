"""Live tests for TelegramTransport."""
import pytest
import os
from chronicler.pipeline import Frame
from chronicler.transports.telegram_transport import TelegramTransport

@pytest.fixture
def token():
    """Get Telegram bot token from environment."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        pytest.skip("TELEGRAM_BOT_TOKEN not set")
    return token

@pytest.fixture
async def transport(token):
    """Create a TelegramTransport instance."""
    transport = TelegramTransport(token)
    yield transport
    await transport.stop()

@pytest.mark.asyncio
async def test_transport_initialization(transport):
    """Test initializing the transport."""
    assert transport.token is not None
    assert transport.app is not None

@pytest.mark.asyncio
async def test_transport_start_stop(transport):
    """Test starting and stopping the transport."""
    await transport.start()
    assert transport.app.running
    await transport.stop()
    assert not transport.app.running 