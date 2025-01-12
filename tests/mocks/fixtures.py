"""Centralized pytest fixtures for testing."""
import os
import shutil
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from pathlib import Path

from tests.mocks.transports import create_mock_telethon, create_mock_telegram_bot

@pytest.fixture
def mock_session_path(tmp_path):
    """Create a temporary directory for Telethon session files."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    
    # Ensure the directory exists and is empty
    if session_dir.exists():
        for file in session_dir.glob("*.session"):
            try:
                file.unlink()
            except Exception:
                pass
            
    yield str(session_dir)
    
    # Cleanup: Close any open connections and remove files
    try:
        for file in session_dir.glob("*.session"):
            try:
                file.unlink()
            except Exception:
                pass
        shutil.rmtree(str(session_dir))
    except Exception:
        pass

@pytest.fixture
def mock_telethon(mock_session_path):
    """Create a mock Telethon client."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock:
        client = create_mock_telethon()
        
        # Mock session with custom path
        client.session = MagicMock()
        client.session.save = MagicMock()
        client.session.session_file = os.path.join(mock_session_path, "test_session.session")
        
        mock.return_value = client
        yield mock

@pytest.fixture
def mock_telegram_bot():
    """Create a mock python-telegram-bot Application."""
    with patch('chronicler.transports.telegram_factory.Application') as mock:
        app = create_mock_telegram_bot()
        
        # Mock builder for token validation
        class MockBuilder:
            def token(self, token):
                if not token:
                    raise ValueError("Token cannot be empty")
                if token == os.environ.get("TELEGRAM_BOT_TOKEN"):
                    return self
                raise ValueError(f"Invalid token: {token}")
            def build(self):
                return app
        app.builder = MagicMock(return_value=MockBuilder())
        
        mock.return_value = app
        yield mock 