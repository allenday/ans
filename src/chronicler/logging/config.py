"""Crystalline logging configuration."""
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
    """A formatter that outputs logs in a crystalline JSON format."""

    def format(self, record):
        """Format the log record into crystalline JSON."""
        crystal = _get_crystal_log(record)
        return json.dumps(crystal)

def configure_logging(level='INFO'):
    """Configure logging with crystalline formatter."""
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
    """Decorator that traces an operation, propagating correlation ID and component."""
    def decorator(func):
        logger = get_logger(func.__module__, component)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get the existing correlation ID before we start
            existing_correlation_id = CORRELATION_ID.get()
            
            # Only generate a new correlation ID if there isn't one
            correlation_id = existing_correlation_id or str(uuid.uuid4())
            CORRELATION_ID.set(correlation_id)
            
            # Save existing context
            existing_component = COMPONENT_ID.get()
            existing_operation = OPERATION_ID.get()
            
            # Set new context
            COMPONENT_ID.set(component)
            OPERATION_ID.set(func.__name__)
            
            # Capture start metrics
            OPERATION_START_TIME.set(time.time())
            process = psutil.Process()
            OPERATION_START_MEMORY.set(process.memory_info().rss / 1024)

            try:
                logger.debug("Operation started", extra={
                    'call_args': str(args),
                    'call_kwargs': str(kwargs)
                })
                result = func(*args, **kwargs)
                logger.debug("Operation completed")
                return result
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
            # Get the existing correlation ID before we start
            existing_correlation_id = CORRELATION_ID.get()
            
            # Only generate a new correlation ID if there isn't one
            correlation_id = existing_correlation_id or str(uuid.uuid4())
            CORRELATION_ID.set(correlation_id)
            
            # Save existing context
            existing_component = COMPONENT_ID.get()
            existing_operation = OPERATION_ID.get()
            
            # Set new context
            COMPONENT_ID.set(component)
            OPERATION_ID.set(func.__name__)
            
            # Capture start metrics
            OPERATION_START_TIME.set(time.time())
            process = psutil.Process()
            OPERATION_START_MEMORY.set(process.memory_info().rss / 1024)

            try:
                logger.debug("Operation started", extra={
                    'call_args': str(args),
                    'call_kwargs': str(kwargs)
                })
                result = await func(*args, **kwargs)
                logger.debug("Operation completed")
                return result
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
    """Get performance metrics from the current context."""
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

def _get_crystal_log(record):
    """Convert a log record into a crystalline format."""
    crystal = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': record.levelname,
        'message': record.getMessage(),
        'location': f"{record.module}:{record.filename}:{record.lineno}",
        'performance': _get_performance_metrics()
    }

    # Add correlation ID if present
    correlation_id = CORRELATION_ID.get()
    if correlation_id:
        crystal['correlation_id'] = correlation_id

    # Add component if present
    component = COMPONENT_ID.get()
    if component:
        crystal['component'] = component

    # Add operation if present
    operation = OPERATION_ID.get()
    if operation:
        crystal['operation'] = operation

    # Add extra context if present
    if hasattr(record, 'call_args'):
        crystal['call_args'] = record.call_args
    if hasattr(record, 'call_kwargs'):
        crystal['call_kwargs'] = record.call_kwargs

    return crystal  # Return dict instead of JSON string 