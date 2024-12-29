from .git import GitStorageAdapter
from .interface import StorageAdapter, User, Topic, Message, Attachment
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  # Avoid "No handler found" warnings

__all__ = ['GitStorageAdapter', 'StorageAdapter', 'User', 'Topic', 'Message', 'Attachment']