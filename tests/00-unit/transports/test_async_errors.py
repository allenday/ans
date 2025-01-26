"""Tests for async error handling."""
import pytest
from chronicler.transports.base import TransportError
from chronicler.logging import get_logger

logger = get_logger(__name__, component="test.transport")

@pytest.fixture
def assert_transport_error_async():
    """Fixture to assert that an async function raises TransportError with expected message."""
    async def _assert_transport_error_async(func, expected_message):
        error_caught = False
        try:
            await func()
        except TransportError as e:
            error_caught = True
            assert str(e) == expected_message
        assert error_caught, f"Expected TransportError with message: {expected_message}"
    return _assert_transport_error_async

async def raise_transport_error_async(message: str):
    """Helper function that raises a TransportError asynchronously."""
    raise TransportError(message)

@pytest.mark.asyncio
async def test_simple_error_async(assert_transport_error_async):
    """Test that we can catch an async TransportError cleanly."""
    error_message = "test async error"
    
    async def raise_error():
        await raise_transport_error_async(error_message)
    
    await assert_transport_error_async(raise_error, error_message) 