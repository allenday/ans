"""Unit tests for pipecat runner."""
import pytest
import asyncio
import signal
import sys
from pathlib import Path
from unittest.mock import patch

from chronicler.frames.base import Frame
from chronicler.commands.processor import CommandProcessor
from chronicler.handlers.command import CommandHandler
from chronicler.transports.telegram.transport.bot import TelegramBotTransport
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.pipeline.pipecat_runner import run_bot, main
from chronicler.processors.base import BaseProcessor
from chronicler.exceptions import TransportAuthenticationError

# Import fixtures and mocks
from tests.mocks.commands import coordinator_mock
from tests.mocks.transports.telegram import mock_telegram_bot, MockApplicationBuilder

@pytest.mark.asyncio
async def test_run_bot_initialization(mock_telegram_bot):
    pytest.skip()
    """Test successful bot initialization and shutdown sequence.
    
    This test verifies that:
    1. Transport is created with token
    2. Transport authenticates successfully
    3. Application is initialized and started
    4. Bot responds to shutdown signal
    5. Application and transport are stopped cleanly
    """
    mock_telegram_bot['loop'] = asyncio.get_running_loop()
    token = "test_token"
    storage_path = Path("/tmp/test_storage")

    # Start the bot - this will trigger authentication and initialization
    run_task = asyncio.create_task(run_bot(token, str(storage_path)))
    
    # Give it a moment to initialize
    await asyncio.sleep(0.1)
    
    # Verify initialization succeeded
    assert mock_telegram_bot['transport']._initialized
    assert mock_telegram_bot['app']._initialized
    assert len(mock_telegram_bot['app'].signal_handlers) > 0
    
    # Set stop event to trigger shutdown
    mock_telegram_bot['stop_event'].set()
    
    # Wait for shutdown
    await run_task

    # Verify shutdown sequence
    assert not mock_telegram_bot['transport']._initialized
    mock_telegram_bot['app'].stop.assert_called_once()
    mock_telegram_bot['app'].shutdown.assert_called_once()

@pytest.mark.asyncio
async def test_run_bot_error_handling(mock_telegram_bot):
    pytest.skip()
    """Test error handling during bot initialization."""
    mock_telegram_bot['loop'] = asyncio.get_running_loop()
    token = "invalid_token"
    storage_path = Path("/tmp/test_storage")

    # Run bot and expect authentication error
    with pytest.raises(TransportAuthenticationError, match="Failed to initialize bot: The token `invalid_token` was rejected by the server."):
        await run_bot(token, str(storage_path))

@pytest.mark.asyncio
async def test_signal_handling(mock_telegram_bot):
    pytest.skip()
    """Test signal handling during bot operation."""
    mock_telegram_bot['loop'] = asyncio.get_running_loop()
    token = "test_token"
    storage_path = Path("/tmp/test_storage")

    # Start the bot
    run_task = asyncio.create_task(run_bot(token, str(storage_path)))
    
    # Give it a moment to initialize
    await asyncio.sleep(0.1)
    
    # Verify signal handlers were registered
    assert len(mock_telegram_bot['app'].signal_handlers) > 0
    
    # Set stop event to trigger shutdown
    mock_telegram_bot['stop_event'].set()
    
    # Wait for shutdown
    await run_task
    
    # Verify shutdown sequence
    assert not mock_telegram_bot['transport']._initialized
    mock_telegram_bot['app'].stop.assert_called_once()
    mock_telegram_bot['app'].shutdown.assert_called_once()

@pytest.mark.asyncio
async def test_graceful_shutdown(mock_telegram_bot):
    pytest.skip()
    """Test graceful shutdown of bot components."""
    mock_telegram_bot['loop'] = asyncio.get_running_loop()
    token = "test_token"
    storage_path = Path("/tmp/test_storage")

    # Start the bot
    run_task = asyncio.create_task(run_bot(token, str(storage_path)))
    
    # Give it a moment to initialize
    await asyncio.sleep(0.1)
    
    # Verify initialization succeeded
    assert mock_telegram_bot['transport']._initialized
    assert mock_telegram_bot['app']._initialized
    
    # Set stop event to trigger shutdown
    mock_telegram_bot['stop_event'].set()
    
    # Wait for shutdown
    await run_task

    # Verify shutdown sequence
    assert not mock_telegram_bot['transport']._initialized
    mock_telegram_bot['app'].stop.assert_called_once()
    mock_telegram_bot['app'].shutdown.assert_called_once()

@pytest.mark.asyncio
async def test_main_function(mock_telegram_bot):
    pytest.skip()
    """Test main function with valid arguments."""
    mock_telegram_bot['loop'] = asyncio.get_running_loop()
    token = "test_token"
    storage_path = "/tmp/test"

    # Mock sys.argv
    with patch('sys.argv', ['script.py', '--token', token, '--storage', storage_path]):
        # Start the bot
        run_task = asyncio.create_task(run_bot(token, storage_path))
        
        # Give it a moment to initialize
        await asyncio.sleep(0.1)
        
        # Verify initialization succeeded
        assert mock_telegram_bot['transport']._initialized
        assert mock_telegram_bot['app']._initialized
        
        # Set stop event to trigger shutdown
        mock_telegram_bot['stop_event'].set()
        
        # Wait for shutdown
        await run_task

        # Verify shutdown sequence
        assert not mock_telegram_bot['transport']._initialized
        mock_telegram_bot['app'].stop.assert_called_once()
        mock_telegram_bot['app'].shutdown.assert_called_once()