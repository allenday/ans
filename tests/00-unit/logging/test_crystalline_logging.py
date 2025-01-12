"""Test crystalline logging system."""
import json
import logging
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from chronicler.logging import (
    configure_logging,
    trace_operation,
    CORRELATION_ID,
    COMPONENT_ID,
    OPERATION_ID
)

@pytest.fixture
def configured_logging():
    """Configure logging for tests."""
    configure_logging(level='DEBUG')
    yield
    # Reset context vars
    CORRELATION_ID.set(None)
    COMPONENT_ID.set(None)
    OPERATION_ID.set(None)

def test_log_format_structure(configured_logging, caplog):
    """Test crystalline log format structure."""
    logger = logging.getLogger('test')
    test_message = "Test log message"
    logger.info(test_message)
    
    assert len(caplog.records) == 1
    record = json.loads(caplog.records[0].message)
    
    # Verify core structure
    assert 'timestamp' in record
    assert 'level' in record
    assert 'correlation_id' in record
    assert 'component' in record
    assert 'operation' in record
    assert 'message' in record
    assert 'location' in record
    assert 'performance' in record
    
    # Verify performance metrics
    assert 'memory_rss_kb' in record['performance']
    assert 'memory_vms_kb' in record['performance']
    assert 'cpu_percent' in record['performance']

@pytest.mark.asyncio
async def test_trace_operation_async(configured_logging, caplog):
    """Test operation tracing for async functions."""
    
    @trace_operation('test.component')
    async def test_operation():
        return "test result"
    
    result = await test_operation()
    
    # Verify operation logs
    assert len(caplog.records) >= 2  # Start and end logs
    
    # Parse log records
    records = [json.loads(r.message) for r in caplog.records]
    
    # Verify correlation ID consistency
    correlation_ids = {r['correlation_id'] for r in records}
    assert len(correlation_ids) == 1  # Same correlation ID across operation
    
    # Verify operation tracking
    assert any(r['message'] == 'Operation started' for r in records)
    assert any(r['message'] == 'Operation completed' for r in records)
    
    # Verify performance metrics
    completion_record = next(r for r in records if r['message'] == 'Operation completed')
    assert 'performance' in completion_record
    assert 'duration_ms' in completion_record['performance']
    assert 'memory_delta_kb' in completion_record['context']

def test_error_logging(configured_logging, caplog):
    """Test error capture in logs."""
    logger = logging.getLogger('test')
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Error occurred", exc_info=True)
    
    assert len(caplog.records) == 1
    record = json.loads(caplog.records[0].message)
    
    # Verify error structure
    assert 'error' in record
    assert record['error']['type'] == 'ValueError'
    assert record['error']['message'] == 'Test error'
    assert 'traceback' in record['error']

@pytest.mark.asyncio
async def test_trace_operation_error(configured_logging, caplog):
    """Test operation tracing with error."""
    
    @trace_operation('test.component')
    async def failing_operation():
        raise ValueError("Operation failed")
    
    with pytest.raises(ValueError):
        await failing_operation()
    
    # Verify error logging
    records = [json.loads(r.message) for r in caplog.records]
    error_record = next(r for r in records if r['level'] == 'ERROR')
    
    assert error_record['error']['type'] == 'ValueError'
    assert error_record['error']['message'] == 'Operation failed'
    assert 'performance' in error_record  # Should still track duration
    assert 'memory_delta_kb' in error_record['context']  # Should track memory impact

def test_context_propagation(configured_logging, caplog):
    """Test context variable propagation."""
    test_correlation_id = "test-correlation-id"
    test_component = "test.component"
    test_operation = "test_operation"
    
    CORRELATION_ID.set(test_correlation_id)
    COMPONENT_ID.set(test_component)
    OPERATION_ID.set(test_operation)
    
    logger = logging.getLogger(test_component)
    logger.info("Test message")
    
    record = json.loads(caplog.records[0].message)
    assert record['correlation_id'] == test_correlation_id
    assert record['component'] == test_component
    assert record['operation'] == test_operation 