"""Exceptions for the chronicler package."""

class ChroniclerError(Exception):
    """Base class for all Chronicler errors."""
    pass

class TransportError(ChroniclerError):
    """Base class for transport-related errors."""
    pass

class TransportConnectionError(TransportError):
    """Raised when transport connection fails."""
    pass

class TransportMessageError(TransportError):
    """Raised when message sending/receiving fails."""
    pass

class TransportAuthenticationError(TransportError):
    """Raised when transport authentication fails or is not performed before required operations."""
    pass

class CommandError(ChroniclerError):
    """Base exception for command-related errors."""
    pass

class CommandValidationError(CommandError):
    """Raised when command validation fails (wrong args, format, etc)."""
    pass

class CommandStorageError(CommandError):
    """Raised when storage operations in a command fail."""
    pass

class CommandAuthorizationError(CommandError):
    """Raised when user is not authorized for a command."""
    pass

class CommandExecutionError(CommandError):
    """Raised when command execution fails for other reasons."""
    pass

class StorageError(ChroniclerError):
    """Base class for storage-related errors."""
    pass

class StorageInitializationError(StorageError):
    """Raised when storage initialization fails."""
    pass

class StorageOperationError(StorageError):
    """Raised when a storage operation fails (save, load, etc)."""
    pass

class StorageValidationError(StorageError):
    """Raised when storage validation fails (metadata, etc)."""
    pass

class ProcessorError(ChroniclerError):
    """Base class for processor-related errors."""
    pass

class ProcessorValidationError(ProcessorError):
    """Raised when processor validation fails (frame type, metadata, etc)."""
    pass

class ProcessorOperationError(ProcessorError):
    """Raised when a processor operation fails."""
    pass

class PipelineError(ChroniclerError):
    """Base class for pipeline-related errors."""
    pass

class PipelineConfigurationError(PipelineError):
    """Raised when pipeline configuration is invalid (wrong processor types, etc)."""
    pass

class PipelineExecutionError(PipelineError):
    """Raised when pipeline execution fails (processor errors, frame transformation errors, etc)."""
    pass

class PipelineShutdownError(PipelineError):
    """Raised when pipeline fails to shutdown gracefully."""
    pass
