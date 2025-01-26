"""Fixtures for transport tests."""
import pytest
from tests.mocks.transports.telegram import mock_telegram_bot

# Re-export the fixture
__all__ = ['mock_telegram_bot'] 