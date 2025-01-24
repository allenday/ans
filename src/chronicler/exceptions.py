"""Exceptions for the chronicler package."""

class TransportError(Exception):
    """Base class for transport-related errors."""
    pass 


class CommandError(Exception):
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
