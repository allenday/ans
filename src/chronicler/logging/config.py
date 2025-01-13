"""Crystalline logging configuration.

This module provides a comprehensive logging system with the following features:
- Structured JSON logging with consistent formatting
- Operation tracing with correlation IDs
- Performance metrics tracking (duration and memory usage)
- Component-based logging with context propagation
- Error tracking with full stack traces
- Async operation support

The logging system is designed to be used across all components of the application
to provide consistent, traceable, and measurable operations.
"""
import logging
import logging.config
import json
import asyncio
from datetime import datetime
import psutil
from typing import Any, Dict, Optional
from functools import wraps
import contextvars
import uuid
import traceback
from datetime import timezone
import sys
import time
import functools

# Context variables for trace propagation
CORRELATION_ID = contextvars.ContextVar('correlation_id', default=None)
COMPONENT_ID = contextvars.ContextVar('component_id', default=None)
OPERATION_ID = contextvars.ContextVar('operation_id', default=None)
OPERATION_START_TIME = contextvars.ContextVar('operation_start_time', default=None)
OPERATION_START_MEMORY = contextvars.ContextVar('operation_start_memory', default=None)

def get_logger(name: str, component: Optional[str] = None) -> logging.Logger:
    """Get a logger with crystalline configuration.
    
    Args:
        name: Logger name (typically __name__)
        component: Optional component identifier
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set component context only if explicitly provided
    if component:
        COMPONENT_ID.set(component)
    else:
        # Reset any existing component context
        COMPONENT_ID.set(None)
    
    # Ensure logger inherits level from root if not explicitly set
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.getLogger().level)
    
    return logger

class CrystallineFormatter(logging.Formatter):
    """A formatter that outputs logs in a crystalline JSON format.
    
    The formatter produces JSON-structured logs with the following fields:
    - timestamp: ISO format UTC timestamp
    - level: Log level (INFO, ERROR, etc.)
    - message: Log message
    - location: Source location (module:file:line)
    - component: Component identifier
    - context: Contextual information including correlation_id and operation_id
    - performance: Performance metrics if available
    - error: Error information if an exception occurred
    """

    def format(self, record):
        """Format the log record into crystalline JSON.
        
        Args:
            record: The LogRecord to format
            
        Returns:
            str: JSON-formatted log entry
        """
        crystal = _get_crystal_log(record)
        return json.dumps(crystal)

def configure_logging(level='INFO'):
    """Configure logging with crystalline formatter.
    
    Sets up the root logger with two handlers:
    1. JSON handler outputting to stdout for structured logging
    2. Standard handler outputting to stderr for caplog compatibility
    
    Args:
        level: The logging level to set (default: 'INFO')
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create handler for JSON output to stdout
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setFormatter(CrystallineFormatter())
    root_logger.addHandler(json_handler)
    
    # Create standard handler for caplog compatibility
    standard_handler = logging.StreamHandler(sys.stderr)
    standard_handler.setFormatter(logging.Formatter('%(levelname)s    %(name)s:%(filename)s:%(lineno)d %(message)s'))
    root_logger.addHandler(standard_handler)

def trace_operation(component: str):
    """Decorator that traces an operation, propagating correlation ID and component.
    
    This decorator provides:
    - Correlation ID generation and propagation
    - Component context tracking
    - Operation ID generation
    - Performance metrics (duration and memory usage)
    - Automatic error logging with stack traces
    - Support for both sync and async functions
    
    Args:
        component: The component identifier for the operation
        
    Returns:
        A decorator function that wraps the target function with tracing
        
    Example:
        @trace_operation('storage')
        async def store_data(data):
            # Function will be automatically traced
            pass
    """
    def decorator(func):
        logger = get_logger(func.__module__, component)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Save existing context
            existing_correlation_id = CORRELATION_ID.get()
            existing_component = COMPONENT_ID.get()
            existing_operation = OPERATION_ID.get()

            # Only generate new correlation ID if one doesn't exist
            if not existing_correlation_id:
                CORRELATION_ID.set(str(uuid.uuid4()))

            # Set component and operation IDs
            COMPONENT_ID.set(component)
            OPERATION_ID.set(str(uuid.uuid4()))

            # Initialize performance tracking
            OPERATION_START_TIME.set(time.time())
            process = psutil.Process()
            OPERATION_START_MEMORY.set(process.memory_info().rss / 1024)  # Convert to KB

            try:
                logger.debug("Operation started", extra={
                    'call_args': str(args),
                    'call_kwargs': str(kwargs)
                })
                result = func(*args, **kwargs)
                metrics = _get_performance_metrics()
                logger.debug("Operation completed", extra={'performance': metrics})
                return result
            except Exception as e:
                metrics = _get_performance_metrics()
                logger.error(f"Operation failed: {str(e)}", exc_info=True, extra={'performance': metrics})
                raise
            finally:
                # Only clear correlation ID if we generated it
                if not existing_correlation_id:
                    CORRELATION_ID.set(None)
                else:
                    # Restore the existing correlation ID
                    CORRELATION_ID.set(existing_correlation_id)
                
                # Restore previous context
                COMPONENT_ID.set(existing_component)
                OPERATION_ID.set(existing_operation)
                OPERATION_START_TIME.set(None)
                OPERATION_START_MEMORY.set(None)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Save existing context
            existing_correlation_id = CORRELATION_ID.get()
            existing_component = COMPONENT_ID.get()
            existing_operation = OPERATION_ID.get()

            # Only generate new correlation ID if one doesn't exist
            if not existing_correlation_id:
                CORRELATION_ID.set(str(uuid.uuid4()))

            # Set component and operation IDs
            COMPONENT_ID.set(component)
            OPERATION_ID.set(str(uuid.uuid4()))

            # Initialize performance tracking
            OPERATION_START_TIME.set(time.time())
            process = psutil.Process()
            OPERATION_START_MEMORY.set(process.memory_info().rss / 1024)  # Convert to KB

            try:
                logger.debug("Operation started", extra={
                    'call_args': str(args),
                    'call_kwargs': str(kwargs)
                })
                result = await func(*args, **kwargs)
                metrics = _get_performance_metrics()
                logger.debug("Operation completed", extra={'performance': metrics})
                return result
            except Exception as e:
                metrics = _get_performance_metrics()
                logger.error(f"Operation failed: {str(e)}", exc_info=True, extra={'performance': metrics})
                raise
            finally:
                # Only clear correlation ID if we generated it
                if not existing_correlation_id:
                    CORRELATION_ID.set(None)
                else:
                    # Restore the existing correlation ID
                    CORRELATION_ID.set(existing_correlation_id)
                
                # Restore previous context
                COMPONENT_ID.set(existing_component)
                OPERATION_ID.set(existing_operation)
                OPERATION_START_TIME.set(None)
                OPERATION_START_MEMORY.set(None)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

def _get_performance_metrics():
    """Get performance metrics from the current context.
    
    Calculates:
    - Operation duration in milliseconds
    - Memory usage delta in kilobytes
    
    Returns:
        dict: Performance metrics with keys:
            - duration_ms: Operation duration in milliseconds
            - memory_delta_kb: Memory usage change in kilobytes
            Returns empty dict if no metrics available
    """
    start_time = OPERATION_START_TIME.get()
    start_memory = OPERATION_START_MEMORY.get()
    if start_time is None or start_memory is None:
        return {}
    
    # Get duration
    duration = time.time() - start_time
    
    # Get memory delta
    process = psutil.Process()
    current_memory = process.memory_info().rss / 1024  # Convert to KB
    memory_delta = current_memory - start_memory
    
    metrics = {
        'duration_ms': int(duration * 1000),
        'memory_delta_kb': int(memory_delta)
    }
    
    return metrics

def _get_crystal_log(record: logging.LogRecord) -> dict:
    """Convert a LogRecord into the crystal log format.
    
    Structures the log record into a standardized format with:
    - Basic log information (timestamp, level, message, location)
    - Component and correlation tracking
    - Performance metrics
    - Error information if present
    - Additional context from the record
    
    Args:
        record: The LogRecord to convert
        
    Returns:
        dict: The structured log data in crystal format
    """
    try:
        message = record.getMessage()
    except (TypeError, ValueError) as e:
        message = str(record.msg)  # Use raw message if formatting fails

    # Get correlation ID and operation ID
    correlation_id = CORRELATION_ID.get()
    operation_id = OPERATION_ID.get()

    # Initialize base structure
    crystal = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": record.levelname,
        "message": message,
        "location": f"{record.name}:{record.filename}:{record.lineno}",
        "component": COMPONENT_ID.get() or record.name,
        "context": {},
        "performance": {}
    }

    # Add correlation ID at root level and in context
    if correlation_id:
        crystal["correlation_id"] = correlation_id
        crystal["context"]["correlation_id"] = correlation_id

    # Add operation ID to context
    if operation_id:
        crystal["context"]["operation_id"] = operation_id

    # Add error information if present
    if record.exc_info:
        exc_type, exc_value, exc_tb = record.exc_info
        crystal["error"] = {
            "type": exc_type.__name__,
            "message": str(exc_value),
            "traceback": traceback.format_exception(exc_type, exc_value, exc_tb)
        }

    # Get performance metrics from context
    metrics = _get_performance_metrics()
    if metrics:
        crystal["performance"].update(metrics)
        # Also add memory_delta_kb to context
        if 'memory_delta_kb' in metrics:
            crystal["context"]["memory_delta_kb"] = metrics['memory_delta_kb']

    # Update context and performance from record.__dict__
    if hasattr(record, "context") and isinstance(record.context, dict):
        crystal["context"].update(record.context)
    
    if hasattr(record, "performance") and isinstance(record.performance, dict):
        crystal["performance"].update(record.performance)
        # Also add memory_delta_kb to context if present
        if 'memory_delta_kb' in record.performance:
            crystal["context"]["memory_delta_kb"] = record.performance['memory_delta_kb']

    return crystal 