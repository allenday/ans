"""Test crystalline logging configuration."""
import logging
import json
import pytest
from datetime import datetime
import asyncio

from chronicler.logging import (
    configure_logging,
    get_logger,
    trace_operation,
    CORRELATION_ID,
    COMPONENT_ID,
    OPERATION_ID
)

def test_logging_configuration(caplog):
    """Test basic logging configuration."""
    configure_logging(level='DEBUG', use_stream_handler=False)
    logger = get_logger('test')
    
    test_message = "Test log message"
    logger.info(test_message)
    
    # Verify log record
    assert len(caplog.records) == 1
    record = json.loads(caplog.records[0].getMessage())
    
    # Verify structure
    assert record['level'] == 'INFO'
    assert record['message'] == test_message
    assert record['component'] == 'test'
    assert 'timestamp' in record
    assert 'performance' in record
    assert 'memory_rss_kb' in record['performance']
    assert 'memory_vms_kb' in record['performance']
    assert 'cpu_percent' in record['performance']

def test_error_logging(caplog):
    """Test error logging with exception details."""
    configure_logging(level='DEBUG', use_stream_handler=False)
    logger = get_logger('test')
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Error occurred", exc_info=True)
    
    # Verify log record
    assert len(caplog.records) == 1
    record = json.loads(caplog.records[0].getMessage())
    
    # Verify error details
    assert record['level'] == 'ERROR'
    assert record['message'] == "Error occurred"
    assert 'error' in record
    assert record['error']['type'] == 'ValueError'
    assert record['error']['message'] == 'Test error'
    assert 'traceback' in record['error']

@pytest.mark.asyncio
async def test_operation_tracing():
    """Test operation tracing decorator."""
    configure_logging(level='DEBUG')
    test_component = "test_component"
    logger = get_logger(test_component)
    
    @trace_operation(test_component)
    async def test_operation(arg1, arg2):
        return f"{arg1}-{arg2}"
    
    # Execute traced operation
    result = await test_operation("hello", "world")
    assert result == "hello-world"
    
    # Verify context variables were set
    assert CORRELATION_ID.get() is not None
    assert COMPONENT_ID.get() == test_component
    assert OPERATION_ID.get() == "test_operation"

def test_context_enrichment(caplog):
    """Test log enrichment with context data."""
    configure_logging(level='DEBUG', use_stream_handler=False)
    logger = get_logger('test')
    
    context_data = {"user": "test_user", "action": "test_action"}
    logger.info("Test with context", extra={"context": context_data})
    
    # Verify log record
    assert len(caplog.records) == 1
    record = json.loads(caplog.records[0].getMessage())
    
    # Verify context
    assert 'context' in record
    assert record['context'] == context_data

def test_performance_metrics(caplog):
    """Test performance metrics in logs."""
    configure_logging(level='DEBUG', use_stream_handler=False)
    logger = get_logger('test')
    
    custom_metrics = {
        "duration_ms": 123.45,
        "memory_delta_kb": 1024
    }
    logger.info("Test with metrics", extra={"performance": custom_metrics})
    
    # Verify log record
    assert len(caplog.records) == 1
    record = json.loads(caplog.records[0].getMessage())
    
    # Verify metrics
    assert 'performance' in record
    for key, value in custom_metrics.items():
        assert record['performance'][key] == value 