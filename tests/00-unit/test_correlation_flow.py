"""Test correlation flow."""
import pytest
import json
import logging
from pathlib import Path
from dataclasses import dataclass

from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.commands.processor import CommandProcessor
from chronicler.commands.handlers import StartCommandHandler
from chronicler.storage.interface import User
from chronicler.transports.telegram_transport import TelegramTransport
from chronicler.logging import configure_logging, get_logger

from tests.mocks.storage import MockStorageCoordinator

@pytest.mark.asyncio
async def test_correlation_flow(tmp_path, caplog):
    """Test correlation ID propagation through transport -> command -> storage chain."""
    with caplog.at_level('DEBUG'):
        # Configure logging
        configure_logging(level='DEBUG')
        logger = get_logger('test')
        
        # Initialize components
        storage = MockStorageCoordinator(storage_path=tmp_path)
        
        processor = CommandProcessor()
        processor.register_handler('/start', StartCommandHandler(storage))
        
        transport = TelegramTransport(token='dummy')
        transport.processor = processor
        
        # Simulate message flow
        frame = await transport.process_frame({
            'message': {
                'text': '/start',
                'chat': {'id': 123},
                'from': {
                    'id': 456,
                    'username': 'test_user'
                }
            }
        })
        
        # Get logs and parse correlation IDs
        logs = []
        for record in caplog.records:
            try:
                log = json.loads(record.message)
                if 'correlation_id' in log:
                    logs.append(log)
            except json.JSONDecodeError:
                continue
        
        # Verify correlation ID propagation
        correlation_ids = {log['correlation_id'] for log in logs}
        assert len(correlation_ids) == 1, "Multiple correlation IDs found"
        
        # Verify logs from each component
        components = {log['component'] for log in logs}
        assert 'transport.telegram' in components, "Missing transport logs"
        assert 'commands.processor' in components, "Missing command processor logs" 