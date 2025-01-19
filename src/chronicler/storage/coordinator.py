"""Coordinates storage operations across multiple backends."""
import asyncio
from pathlib import Path
import sqlite3
from functools import wraps
from typing import Union, Optional
import time

from chronicler.storage.git import GitStorageAdapter
from chronicler.logging import get_logger, trace_operation

logger = get_logger(__name__)

def retry_on_db_locked(max_retries=3, delay=0.1):
    """Retry an operation if the database is locked."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Database locked, retrying in {delay}s")
                        time.sleep(delay)
                        continue
                    raise
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class StorageCoordinator:
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.git_storage = GitStorageAdapter(self.base_path)
        self.logger = logger.getChild(self.__class__.__name__)

    @trace_operation('storage.coordinator')
    @retry_on_db_locked()
    def init_storage(self, user_id: int) -> None:
        """Initialize storage for a user."""
        self.git_storage.init_storage(user_id)

    @trace_operation('storage.coordinator')
    @retry_on_db_locked()
    def create_topic(self, user_id: int, topic_name: str) -> None:
        """Create a new topic for a user."""
        self.git_storage.create_topic(user_id, topic_name)

    @trace_operation('storage.coordinator')
    @retry_on_db_locked()
    def save_message(self, user_id: int, topic_name: str, message: dict) -> None:
        """Save a message to a topic."""
        self.git_storage.save_message(user_id, topic_name, message)

    @trace_operation('storage.coordinator')
    @retry_on_db_locked()
    def save_attachment(self, user_id: int, topic_name: str, file_path: str | Path, attachment_name: str) -> None:
        """Save an attachment to a topic."""
        self.git_storage.save_attachment(user_id, topic_name, file_path, attachment_name)

    @trace_operation('storage.coordinator')
    @retry_on_db_locked()
    def sync(self, user_id: int) -> None:
        """Sync changes with remote storage."""
        self.git_storage.sync(user_id)

    @trace_operation('storage.coordinator')
    def set_github_config(self, token: str, repo: str) -> None:
        """Set GitHub configuration for Git storage."""
        self.git_storage.set_github_config(token, repo)

    @trace_operation('storage.coordinator')
    def stop(self) -> None:
        """Stop all storage operations."""
        pass

    @trace_operation('storage.coordinator')
    def topic_exists(self, user_id: int, topic_name: str) -> bool:
        """Check if a topic exists."""
        return self.git_storage.topic_exists(user_id, topic_name) 