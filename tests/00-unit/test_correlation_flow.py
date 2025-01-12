"""Test correlation flow."""
import asyncio
import pytest
import json
import logging
import sys
from io import StringIO
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
async def test_correlation_flow(tmp_path, caplog, capsys):
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
        
        # Clear stdout before processing frame
        capsys.readouterr()
        
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
        
        # Get logs from stdout (JSON logs)
        stdout, _ = capsys.readouterr()
        logs = []
        for line in stdout.splitlines():
            try:
                log = json.loads(line)
                if 'correlation_id' in log:
                    logs.append(log)
            except json.JSONDecodeError:
                continue
        
        # Print all logs for debugging
        print("\nFound logs with correlation IDs:")
        for log in logs:
            print(f"Log: {log}")
        
        # Verify correlation ID propagation
        correlation_ids = {log['correlation_id'] for log in logs}
        assert len(correlation_ids) == 1, f"Multiple correlation IDs found: {correlation_ids}" 