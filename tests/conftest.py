"""Test configuration and fixtures."""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
import logging

from chronicler.storage.coordinator import StorageCoordinator
from chronicler.storage.git import GitStorageAdapter

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)
    
@pytest.fixture
def storage_path(temp_dir):
    """Create a temporary storage path."""
    storage_path = Path(temp_dir) / "storage"
    storage_path.mkdir()
    return storage_path 

@pytest.fixture(autouse=True)
def disable_custom_logging():
    """Disable custom logging configuration during tests."""
    # Store original configure_logging function
    from chronicler.logging.config import configure_logging
    original_configure = configure_logging
    
    # Replace with no-op function
    def no_op_configure(*args, **kwargs):
        pass
    
    from chronicler.logging import config
    config.configure_logging = no_op_configure
    
    # Run the test
    yield
    
    # Restore original function
    config.configure_logging = original_configure 