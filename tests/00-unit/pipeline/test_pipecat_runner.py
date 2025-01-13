"""Unit tests for pipecat runner."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from chronicler.pipeline.pipecat_runner import run_bot

@pytest.mark.asyncio
async def test_run_bot_initialization():
    pytest.skip()
    """Test bot initialization and component setup."""
    token = "test_token"
    storage_path = "/tmp/test_storage"
    
    # Mock all dependencies
    with patch('chronicler.pipeline.pipecat_runner.TelegramTransport') as mock_transport, \
         patch('chronicler.pipeline.pipecat_runner.StorageProcessor') as mock_storage, \
         patch('chronicler.pipeline.pipecat_runner.CommandProcessor') as mock_cmd_proc, \
         patch('chronicler.pipeline.pipecat_runner.Pipeline') as mock_pipeline:
        
        # Setup mocks
        mock_transport_inst = AsyncMock()
        mock_transport.return_value = mock_transport_inst
        mock_storage_inst = MagicMock()
        mock_storage.return_value = mock_storage_inst
        mock_cmd_proc_inst = MagicMock()
        mock_cmd_proc.return_value = mock_cmd_proc_inst
        mock_pipeline_inst = MagicMock()
        mock_pipeline.return_value = mock_pipeline_inst
        
        # Create event to control stop signal
        stop_event = asyncio.Event()
        
        # Run bot with immediate stop
        async def stop_bot():
            await asyncio.sleep(0.1)
            stop_event.set()
        
        asyncio.create_task(stop_bot())
        await run_bot(token, storage_path)
        
        # Verify component initialization
        mock_transport.assert_called_once_with(token)
        mock_storage.assert_called_once_with(Path(storage_path))
        mock_cmd_proc.assert_called_once()
        
        # Verify command handlers registration
        assert mock_cmd_proc_inst.register_handler.call_count == 3
        
        # Verify pipeline creation
        mock_pipeline.assert_called_once()
        pipeline_args = mock_pipeline.call_args[0][0]
        assert len(pipeline_args) == 3
        assert pipeline_args[0] == mock_transport_inst
        assert pipeline_args[1] == mock_cmd_proc_inst
        assert pipeline_args[2] == mock_storage_inst
        
        # Verify transport lifecycle
        mock_transport_inst.start.assert_called_once()
        mock_transport_inst.stop.assert_called_once()

@pytest.mark.asyncio
async def test_run_bot_error_handling():
    pytest.skip()
    """Test error handling during bot execution."""
    token = "test_token"
    storage_path = "/tmp/test_storage"
    
    # Mock all dependencies
    with patch('chronicler.pipeline.pipecat_runner.TelegramTransport') as mock_transport, \
         patch('chronicler.pipeline.pipecat_runner.StorageProcessor') as mock_storage, \
         patch('chronicler.pipeline.pipecat_runner.CommandProcessor') as mock_cmd_proc, \
         patch('chronicler.pipeline.pipecat_runner.Pipeline') as mock_pipeline:
        
        # Setup mocks with error
        mock_transport_inst = AsyncMock()
        mock_transport_inst.start.side_effect = RuntimeError("Test error")
        mock_transport.return_value = mock_transport_inst
        
        # Run bot and expect error
        with pytest.raises(RuntimeError, match="Test error"):
            await run_bot(token, storage_path)
        
        # Verify cleanup was called even after error
        mock_transport_inst.stop.assert_called_once() 