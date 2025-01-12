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

# Context variables for trace propagation
CORRELATION_ID = contextvars.ContextVar('correlation_id', default=None)
COMPONENT_ID = contextvars.ContextVar('component_id', default=None)
OPERATION_ID = contextvars.ContextVar('operation_id', default=None)

def get_logger(name: str, component: Optional[str] = None) -> logging.Logger:
    """Get a logger with crystalline configuration.
    
    Args:
        name: Logger name (typically __name__)
        component: Optional component identifier
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if component:
        COMPONENT_ID.set(component)
    return logger

class CrystallineFormatter(logging.Formatter):
    """Crystalline log formatter that enforces a structured log output."""

    def format(self, record):
        """Format the log record into a crystalline structure."""
        # Format message with args if present
        try:
            if record.args:
                message = record.msg % record.args
            else:
                message = record.msg
        except TypeError:
            message = record.msg

        # Build base performance metrics
        performance = {
            'memory_rss_kb': psutil.Process().memory_info().rss / 1024,
            'memory_vms_kb': psutil.Process().memory_info().vms / 1024,
            'cpu_percent': psutil.Process().cpu_percent()
        }

        # Merge additional performance metrics from extra if present
        if hasattr(record, 'performance'):
            performance.update(record.performance)

        # Build crystalline structure
        crystal = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'correlation_id': CORRELATION_ID.get(),
            'component': COMPONENT_ID.get() or record.name,
            'operation': OPERATION_ID.get(),
            'message': message,
            'location': f"{record.pathname}:{record.lineno}",
            'performance': performance
        }

        # Add error details if present
        if record.exc_info:
            crystal['error'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }

        # Add additional context if provided
        if hasattr(record, 'context'):
            crystal['context'] = record.context

        # Return the JSON string
        return json.dumps(crystal)

def configure_logging(level='INFO'):
    """Configure logging with crystalline formatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create handler that writes to stdout for pytest compatibility
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CrystallineFormatter())
    root_logger.addHandler(handler)

def trace_operation(component: str):
    """Decorator for operation tracing with correlation."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            correlation_id = CORRELATION_ID.get() or str(uuid.uuid4())
            operation_id = f"{func.__name__}"
            
            CORRELATION_ID.set(correlation_id)
            COMPONENT_ID.set(component)
            OPERATION_ID.set(operation_id)
            
            logger = logging.getLogger(component)
            start_time = datetime.utcnow()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                logger.debug("Operation started", extra={
                    'context': {'args': args, 'kwargs': kwargs}
                })
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                memory_delta = (psutil.Process().memory_info().rss - start_memory) / 1024
                
                logger.debug("Operation completed", extra={
                    'context': {
                        'result': str(result) if result else None,
                        'memory_delta_kb': memory_delta
                    },
                    'performance': {
                        'duration_ms': duration
                    }
                })
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                memory_delta = (psutil.Process().memory_info().rss - start_memory) / 1024
                logger.error(f"Operation failed: {str(e)}", 
                           exc_info=True,
                           extra={
                               'context': {'memory_delta_kb': memory_delta},
                               'performance': {'duration_ms': duration}
                           })
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            correlation_id = CORRELATION_ID.get() or str(uuid.uuid4())
            operation_id = f"{func.__name__}"
            
            CORRELATION_ID.set(correlation_id)
            COMPONENT_ID.set(component)
            OPERATION_ID.set(operation_id)
            
            logger = logging.getLogger(component)
            start_time = datetime.utcnow()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                logger.debug("Operation started", extra={
                    'context': {'args': args, 'kwargs': kwargs}
                })
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                memory_delta = (psutil.Process().memory_info().rss - start_memory) / 1024
                
                logger.debug("Operation completed", extra={
                    'context': {
                        'result': str(result) if result else None,
                        'memory_delta_kb': memory_delta
                    },
                    'performance': {
                        'duration_ms': duration
                    }
                })
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                memory_delta = (psutil.Process().memory_info().rss - start_memory) / 1024
                logger.error(f"Operation failed: {str(e)}", 
                           exc_info=True,
                           extra={
                               'context': {'memory_delta_kb': memory_delta},
                               'performance': {'duration_ms': duration}
                           })
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 