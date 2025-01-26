"""Test crystalline logging configuration."""
from chronicler.logging import logging
import json
import pytest
from datetime import datetime
import asyncio
from contextlib import contextmanager
from chronicler.logging.config import CrystallineFormatter

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

def test_sync_operation_tracing(caplog):
    """Test operation tracing with sync functions."""
    with capture_logs() as (stdout, stderr):
        configure_logging(level='DEBUG')
        logger = get_logger('test')

        @trace_operation('test_component')
        def test_operation():
            logger.info("Inside traced operation")
            return "success"

        result = test_operation()
        assert result == "success"

        # Get JSON output
        output = stdout.getvalue().strip().split('\n')
        start_log = json.loads(output[0])
        end_log = json.loads(output[-1])

        # Verify correlation ID propagation
        assert start_log['correlation_id'] == end_log['correlation_id']
        assert start_log['component'] == 'test_component'
        assert 'performance' in end_log
        assert 'duration_ms' in end_log['performance']

def test_operation_tracing_error_handling(caplog):
    """Test operation tracing with error handling."""
    with capture_logs() as (stdout, stderr):
        configure_logging(level='DEBUG')
        logger = get_logger('test')

        @trace_operation('test_component')
        def failing_operation():
            logger.info("About to fail")
            raise ValueError("Test failure")

        with pytest.raises(ValueError, match="Test failure"):
            failing_operation()

        # Get JSON output
        output = stdout.getvalue().strip().split('\n')
        start_log = json.loads(output[0])
        error_log = json.loads(output[-1])

        # Verify error logging
        assert error_log['level'] == 'ERROR'
        assert 'Test failure' in error_log['message']
        assert error_log['error']['type'] == 'ValueError'
        assert 'performance' in error_log
        assert 'duration_ms' in error_log['performance']

def test_component_context_propagation(caplog):
    """Test component context propagation."""
    with capture_logs() as (stdout, stderr):
        configure_logging(level='DEBUG')
        
        # Test explicit component
        logger1 = get_logger('test1', component='custom_component')
        logger1.info("Test message 1")
        
        # Test inherited component
        logger2 = get_logger('test2')
        logger2.info("Test message 2")
        
        output = stdout.getvalue().strip().split('\n')
        log1 = json.loads(output[0])
        log2 = json.loads(output[1])
        
        assert log1['component'] == 'custom_component'
        assert log2['component'] == 'test2'

def test_log_level_inheritance(caplog):
    """Test log level inheritance and override."""
    with capture_logs() as (stdout, stderr):
        # Configure root logger as INFO
        configure_logging(level='INFO')
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        
        # Create child logger and verify inheritance
        child_logger = get_logger('test.child')
        assert child_logger.level == logging.INFO
        
        # Override child logger level
        child_logger.setLevel(logging.DEBUG)
        assert child_logger.level == logging.DEBUG
        assert root_logger.level == logging.INFO  # Root unchanged

def test_nested_operation_tracing(caplog):
    """Test nested operation tracing."""
    with capture_logs() as (stdout, stderr):
        configure_logging(level='DEBUG')
        logger = get_logger('test')

        @trace_operation('outer')
        def outer_operation():
            logger.info("In outer")
            return inner_operation()

        @trace_operation('inner')
        def inner_operation():
            logger.info("In inner")
            return "success"

        result = outer_operation()
        assert result == "success"

        # Get JSON output
        output = stdout.getvalue().strip().split('\n')
        logs = [json.loads(line) for line in output]
        
        # Find operation logs
        outer_start = next(log for log in logs if log['message'] == "Operation started" and log['component'] == 'outer')
        inner_start = next(log for log in logs if log['message'] == "Operation started" and log['component'] == 'inner')
        
        # Verify correlation ID propagation
        assert outer_start['correlation_id'] == inner_start['correlation_id']
        assert outer_start['component'] == 'outer'
        assert inner_start['component'] == 'inner' 

def test_formatter_error_handling(caplog):
    """Test error handling in message formatting."""
    logger = get_logger(__name__)
    
    # Create a record with invalid args
    record = logging.LogRecord(
        name=__name__,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Test %s %s",
        args=("one",),  # Missing second argument
        exc_info=None,
        func=None
    )
    
    # Format the record directly
    formatter = CrystallineFormatter()
    log_output = formatter.format(record)
    log_data = json.loads(log_output)
    
    assert log_data["message"] == "Test %s %s"  # Original message preserved
    assert log_data["level"] == "INFO"
    assert log_data["component"] == __name__

@pytest.mark.asyncio
async def test_trace_operation_error_handling(caplog):
    """Test error handling in trace_operation decorator."""
    @trace_operation("test_component")
    async def failing_operation():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError, match="Test error"):
        await failing_operation()
    
    error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_logs) == 1
    
    # Get the formatted log message
    formatter = CrystallineFormatter()
    log_output = formatter.format(error_logs[0])
    log_data = json.loads(log_output)
    
    assert "Operation failed: Test error" in log_data["message"]
    assert log_data["error"]["type"] == "ValueError"
    assert "memory_delta_kb" in log_data["context"]
    assert "duration_ms" in log_data["performance"] 