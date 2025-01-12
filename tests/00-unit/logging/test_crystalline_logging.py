"""Test crystalline logging configuration."""
import logging
import json
import pytest
from datetime import datetime
import asyncio
from contextlib import contextmanager

from chronicler.logging import (
    configure_logging,
    get_logger,
    trace_operation,
    CORRELATION_ID,
    COMPONENT_ID,
    OPERATION_ID
)

@contextmanager
def capture_logs():
    """Helper to capture logs from stdout/stderr."""
    import sys
    from io import StringIO
    stdout = StringIO()
    stderr = StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = stdout
        sys.stderr = stderr
        yield stdout, stderr
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

def test_logging_configuration(caplog):
    """Test basic logging configuration."""
    with capture_logs() as (stdout, stderr):
        configure_logging(level='DEBUG')
        logger = get_logger('test')
        
        test_message = "Test log message"
        logger.info(test_message)
        
        # Get JSON output
        output = stdout.getvalue()
        log_data = json.loads(output.strip().split('\n')[-1])
        
        # Verify log record
        assert log_data['level'] == 'INFO'
        assert log_data['message'] == test_message
        assert log_data['component'] == 'test'

def test_error_logging(caplog):
    """Test error logging with exception details."""
    with capture_logs() as (stdout, stderr):
        configure_logging(level='DEBUG')
        logger = get_logger('test')
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.error("Error occurred", exc_info=True)
        
        # Get JSON output
        output = stdout.getvalue()
        log_data = json.loads(output.strip().split('\n')[-1])
        
        # Verify log record
        assert log_data['level'] == 'ERROR'
        assert log_data['message'] == "Error occurred"
        assert 'error' in log_data
        assert log_data['error']['type'] == 'ValueError'
        assert log_data['error']['message'] == 'Test error'

def test_operation_tracing(caplog):
    """Test operation tracing with correlation ID."""
    configure_logging(level='DEBUG')
    logger = get_logger('test')

    @trace_operation('test_component')
    async def test_operation():
        logger.info("Inside traced operation")
        return "success"

    import asyncio
    result = asyncio.run(test_operation())
    assert result == "success"

def test_context_enrichment(caplog):
    """Test log enrichment with context data."""
    with capture_logs() as (stdout, stderr):
        configure_logging(level='DEBUG')
        logger = get_logger('test')
        
        context_data = {"user": "test_user", "action": "test_action"}
        logger.info("Test with context", extra={"context": context_data})
        
        # Get JSON output
        output = stdout.getvalue()
        log_data = json.loads(output.strip().split('\n')[-1])
        
        # Verify log record
        assert log_data['level'] == 'INFO'
        assert log_data['message'] == "Test with context"
        assert 'context' in log_data
        assert log_data['context'] == context_data

def test_performance_metrics(caplog):
    """Test performance metrics in logs."""
    with capture_logs() as (stdout, stderr):
        configure_logging(level='DEBUG')
        logger = get_logger('test')
        
        custom_metrics = {
            "duration_ms": 123.45,
            "memory_delta_kb": 1024
        }
        logger.info("Test with metrics", extra={"performance": custom_metrics})
        
        # Get JSON output
        output = stdout.getvalue()
        log_data = json.loads(output.strip().split('\n')[-1])
        
        # Verify log record
        assert log_data['level'] == 'INFO'
        assert log_data['message'] == "Test with metrics"
        assert 'performance' in log_data
        assert log_data['performance']['duration_ms'] == custom_metrics['duration_ms']
        assert log_data['performance']['memory_delta_kb'] == custom_metrics['memory_delta_kb'] 