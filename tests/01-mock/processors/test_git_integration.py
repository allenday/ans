import pytest
import os
import git
import asyncio
from pathlib import Path
from unittest.mock import patch
from chronicler.pipeline import TextFrame, ImageFrame
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.services.git_sync_service import GitSyncService

@pytest.fixture
def storage_path(tmp_path):
    """Create a temporary storage path."""
    return tmp_path / "storage"

@pytest.fixture
def git_config():
    """Git configuration for testing."""
    return {
        'GIT_REPO_URL': 'https://github.com/test/repo.git',
        'GIT_BRANCH': 'main',
        'GIT_USERNAME': 'testuser',
        'GIT_ACCESS_TOKEN': 'testtoken',
        'GIT_SYNC_INTERVAL': '1'  # 1 second for faster testing
    }

@pytest.mark.integration
class TestGitIntegration:
    """Integration tests for git functionality."""
    
    async def test_message_commit_and_sync(self, storage_path, git_config):
        """Test the complete flow of committing a message and syncing."""
        # Setup environment
        with patch.dict('os.environ', git_config):
            # Initialize processor and service
            processor = StorageProcessor(storage_path)
            sync_service = GitSyncService(
                processor.git_processor,
                sync_interval=1
            )
            
            try:
                # Start sync service
                await sync_service.start()
                
                # Create and process a text frame
                frame = TextFrame("test message")
                frame.metadata = {
                    'chat_id': 123,
                    'thread_id': 456,
                    'chat_title': 'Test Chat'
                }
                
                # Process frame (should trigger commit)
                await processor.process_frame(frame)
                
                # Wait for sync
                await asyncio.sleep(2)
                
                # Verify git repository state
                repo = git.Repo(str(storage_path))
                
                # Check commit
                assert repo.head.commit.message.startswith("Add message")
                
                # Check remote
                origin = repo.remote('origin')
                assert origin.url == git_config['GIT_REPO_URL'].replace(
                    'https://',
                    f"https://{git_config['GIT_USERNAME']}:{git_config['GIT_ACCESS_TOKEN']}@"
                )
                
            finally:
                # Cleanup
                await sync_service.stop()
    
    async def test_media_commit_and_sync(self, storage_path, git_config):
        """Test committing media files and syncing."""
        # Setup environment
        with patch.dict('os.environ', git_config):
            # Initialize processor and service
            processor = StorageProcessor(storage_path)
            sync_service = GitSyncService(
                processor.git_processor,
                sync_interval=1
            )
            
            try:
                # Start sync service
                await sync_service.start()
                
                # Create and process an image frame
                frame = ImageFrame(b"test_image_data", "jpg")
                frame.metadata = {
                    'chat_id': 123,
                    'thread_id': 456,
                    'chat_title': 'Test Chat',
                    'file_id': 'test_image'
                }
                
                # Process frame (should trigger commits)
                await processor.process_frame(frame)
                
                # Wait for sync
                await asyncio.sleep(2)
                
                # Verify git repository state
                repo = git.Repo(str(storage_path))
                
                # Check commits
                commits = list(repo.iter_commits())
                assert any("Add media files" in c.message for c in commits)
                assert any("Add message" in c.message for c in commits)
                
                # Verify files exist and are tracked
                message_file = next(repo.tree().traverse()).path
                assert message_file.startswith("messages/")
                media_file = next(
                    f for f in repo.tree().traverse()
                    if f.path.startswith("media/")
                )
                assert media_file.path.endswith(".jpg")
                
            finally:
                # Cleanup
                await sync_service.stop()
    
    async def test_sync_retry_on_failure(self, storage_path, git_config):
        """Test sync retry behavior on push failure."""
        # Setup environment
        with patch.dict('os.environ', git_config):
            # Initialize processor and service
            processor = StorageProcessor(storage_path)
            sync_service = GitSyncService(
                processor.git_processor,
                sync_interval=1,
                max_retries=2,
                retry_delay=1
            )
            
            try:
                # Start sync service
                await sync_service.start()
                
                # Create and process a text frame
                frame = TextFrame("test message")
                frame.metadata = {
                    'chat_id': 123,
                    'thread_id': 456,
                    'chat_title': 'Test Chat'
                }
                
                # Process frame
                await processor.process_frame(frame)
                
                # Mock push failure then success
                with patch.object(
                    processor.git_processor._repo.remotes.origin,
                    'push',
                    side_effect=[Exception("Network error"), None]
                ):
                    # Wait for retry and success
                    await asyncio.sleep(3)
                
                # Verify final state
                repo = git.Repo(str(storage_path))
                assert repo.head.commit.message.startswith("Add message")
                
            finally:
                # Cleanup
                await sync_service.stop()