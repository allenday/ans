"""
User Story: User Authentication Setup
As a new user, I want to set up my user account with the bot
so that it can archive messages on my behalf.

Scenario:
1. Initial Authentication Flow:
   - User messages bot with /start
   - Bot requests Telegram API credentials (API_ID, API_HASH)
   - User provides credentials
   - Bot attempts to create user client session
   - Telegram sends OTP to user's Telegram account
   - User forwards OTP to bot
   - Bot completes authentication and stores session data

Architecture Notes:
- Multi-tenant Considerations (Future):
  - Session data needs to be stored per-user
  - Frame processing must be user-specific
  - Storage paths should be user-isolated
  - Git repositories should be user-specific
  - Commands should only affect user's own config

Current Implementation Scope:
- Single-user mode only
- Authentication flow works for one user
- Session data stored in single location
- No user isolation in storage/processing

Future Enhancement Notes:
- Add user session management
- Implement session data isolation
- Add user-specific storage paths
- Add user-specific Git repos
- Add user permission checks
"""

import pytest
import pytest_asyncio
import os
from pathlib import Path

from chronicler.transports.telegram_factory import TelegramTransportFactory
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.storage.coordinator import StorageCoordinator

@pytest.fixture
def storage_path(tmp_path):
    """Provide a temporary directory for test storage"""
    test_storage = tmp_path / "test_storage"
    test_storage.mkdir(parents=True, exist_ok=True)
    return test_storage

@pytest.fixture
def storage_coordinator(storage_path):
    """Create a storage coordinator instance"""
    return StorageCoordinator(storage_path)

@pytest_asyncio.fixture
async def telegram_factory():
    """Create a telegram transport factory for tests"""
    return TelegramTransportFactory()

@pytest_asyncio.fixture
async def bot_transport(telegram_factory):
    """Create and initialize a bot transport"""
    bot_token = os.getenv("TEST_BOT_TOKEN")
    if not bot_token:
        pytest.skip("TEST_BOT_TOKEN environment variable not set")
    
    transport = await telegram_factory.create_bot_transport(bot_token)
    await transport.start()
    yield transport
    await transport.stop()

@pytest_asyncio.fixture
async def user_transport(telegram_factory):
    """Create and initialize a user transport"""
    api_id = os.getenv("TEST_API_ID")
    api_hash = os.getenv("TEST_API_HASH")
    phone = os.getenv("TEST_PHONE")
    
    if not all([api_id, api_hash, phone]):
        pytest.skip("TEST_API_ID, TEST_API_HASH, or TEST_PHONE environment variables not set")
    
    transport = await telegram_factory.create_user_transport(
        api_id=int(api_id),
        api_hash=api_hash,
        phone=phone
    )
    await transport.start()
    yield transport
    await transport.stop()

@pytest.mark.asyncio
async def test_user_authentication_story(
    storage_path,
    storage_coordinator,
    bot_transport,
    user_transport,
    caplog
):
    """Test the user authentication flow"""
    caplog.set_level(logging.INFO)
    
    # 1. User sends /start to bot
    start_frame = CommandFrame(
        command="/start",
        args=[],
        metadata={
            "chat_id": os.getenv("TEST_CHAT_ID"),
            "user_id": os.getenv("TEST_USER_ID")
        }
    )
    await bot_transport.process_frame(start_frame)
    
    # 2. Bot should request API credentials
    # Verify bot response requesting credentials
    assert any("Please provide your Telegram API credentials" in record.message 
              for record in caplog.records)
    
    # 3. User provides API credentials
    credentials_frame = TextFrame(
        text=f"/config {os.getenv('TEST_API_ID')} {os.getenv('TEST_API_HASH')}",
        metadata={
            "chat_id": os.getenv("TEST_CHAT_ID"),
            "user_id": os.getenv("TEST_USER_ID")
        }
    )
    await bot_transport.process_frame(credentials_frame)
    
    # 4. Verify credentials are stored
    session_file = storage_path / "sessions" / f"{os.getenv('TEST_USER_ID')}.session"
    assert session_file.exists(), "Session file should be created"
    
    # 5. Verify successful authentication message
    assert any("Authentication successful" in record.message 
              for record in caplog.records) 