"""Test correlation ID propagation through the pipeline."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import asyncio

from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.commands.processor import CommandProcessor
from chronicler.handlers.command import StartCommandHandler, ConfigCommandHandler, StatusCommandHandler
from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from chronicler.logging import configure_logging, get_logger
from tests.mocks.transports.telegram import mock_telegram_bot
from chronicler.logging.config import CORRELATION_ID

@pytest.mark.asyncio
async def test_correlation_flow(mock_telegram_bot, tmp_path, caplog, capsys):
    """Test correlation ID propagation through transport -> command -> storage chain."""
    mock_telegram_bot['loop'] = asyncio.get_running_loop()
    with caplog.at_level('DEBUG'):
        # Configure logging and set correlation ID
        configure_logging(level='DEBUG')
        CORRELATION_ID.set('test-correlation-id')
        logger = get_logger('test')

        # Initialize components
        storage = AsyncMock()
        storage.init_storage = AsyncMock()
        storage.create_topic = AsyncMock()
        storage.is_initialized = AsyncMock(return_value=False)
        storage.set_github_config = AsyncMock()
        storage.sync = AsyncMock()
        storage.save_message = AsyncMock()

        # Create command processor and register handlers
        processor = CommandProcessor(coordinator=storage)
        start_handler = StartCommandHandler(coordinator=storage)
        config_handler = ConfigCommandHandler(coordinator=storage)
        status_handler = StatusCommandHandler(coordinator=storage)

        # Register handlers
        processor.register_command("/start", start_handler.handle)
        processor.register_command("/config", config_handler.handle)
        processor.register_command("/status", status_handler.handle)

        # Get transport from mock_telegram_bot fixture and set storage
        transport = mock_telegram_bot['transport']
        transport.storage = storage  # Set storage object
        transport.frame_processor = processor.process
        
        # Authenticate and initialize transport
        await transport.authenticate()
        await transport.start()

        # Create a proper command frame
        frame = CommandFrame(
            command="/start",
            args=[],
            metadata={
                'chat_id': 123,
                'chat_title': "Test Chat",
                'sender_id': 456,
                'sender_name': "testuser",
                'message_id': 789,
                'timestamp': datetime.now(timezone.utc).timestamp(),
                'thread_id': 'default',
                'correlation_id': 'test-correlation-id'  # Add correlation ID to metadata
            }
        )

        # Process the frame through transport's command handler
        response = await processor.process(frame)
        assert response is not None
        assert response.metadata['correlation_id'] == 'test-correlation-id'
        assert storage.init_storage.call_count == 1
        assert storage.create_topic.call_count == 1

        # Verify storage calls
        storage.is_initialized.assert_awaited_once()
        storage.init_storage.assert_awaited_once()
        storage.create_topic.assert_awaited_once()
        storage.save_message.assert_awaited_once()

        # Verify logs contain correlation ID
        log_output = capsys.readouterr().out
        assert 'test-correlation-id' in log_output