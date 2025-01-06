import pytest
import pytest_asyncio
import os
import shutil
from pathlib import Path
from chronicler.storage.interface import User
from chronicler.storage.git import GitStorageAdapter

@pytest_asyncio.fixture
async def git_adapter_live(tmp_path):
    """Create a real GitStorageAdapter with a real git repo"""
    # Clean up any existing test data
    test_path = tmp_path / "test_user_journal"
    if test_path.exists():
        shutil.rmtree(test_path)
    
    # Create storage adapter
    storage = GitStorageAdapter(tmp_path)
    user = User(id="test_user", name="Test User")
    await storage.init_storage(user)
    
    return storage 