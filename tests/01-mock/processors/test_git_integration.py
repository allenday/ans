import pytest
import os
import git
import asyncio
from pathlib import Path
from unittest.mock import patch
from chronicler.frames import TextFrame, ImageFrame
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.services.git_sync_service import GitSyncService

@pytest.fixture
def storage_path(tmp_path):
    """Create a temporary storage path."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True)
    
    # Initialize Git repository
    repo = git.Repo.init(storage_dir)
    
    # Configure Git user for commits
    with repo.config_writer() as git_config:
        git_config.set_value('user', 'name', 'Test User')
        git_config.set_value('user', 'email', 'test@example.com')
    
    # Create initial structure
    messages_dir = storage_dir / "messages"
    media_dir = storage_dir / "media"
    messages_dir.mkdir()
    media_dir.mkdir()
    
    # Add and commit initial structure
    repo.index.add([str(messages_dir), str(media_dir)])
    repo.index.commit("Initial commit")
    
    # Create and checkout main branch if it doesn't exist
    try:
        repo.git.branch('main')
    except git.exc.GitCommandError as e:
        if 'already exists' not in str(e):
            raise
    repo.git.checkout('main')
    
    return storage_dir

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
    
    @pytest.mark.asyncio
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
                frame = TextFrame(content="test message")
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
                assert repo.head.commit.message.startswith("Added message to topic")
                assert "456" in repo.head.commit.message
                
                # Check remote
                origin = repo.remote('origin')
                assert origin.url == git_config['GIT_REPO_URL'].replace(
                    'https://',
                    f"https://{git_config['GIT_USERNAME']}:{git_config['GIT_ACCESS_TOKEN']}@"
                )
                
            finally:
                # Cleanup
                await sync_service.stop()
    
    @pytest.mark.asyncio
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
                frame = ImageFrame(
                    content=b"test_image_data",
                    size=(100, 100),  # Mock image size
                    format="jpg"
                )
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
                assert any("Added message to topic" in c.message for c in commits)
                assert any("456" in c.message for c in commits)
                assert any("attachments" in c.message for c in commits)
                
                # Verify files exist and are tracked
                files = [item.path for item in repo.tree().traverse()]
                assert any(f.startswith("telegram/") for f in files), "No telegram files found"
                assert any("messages.jsonl" in f for f in files), "No messages file found"
                assert any("test_image.jpg" in f for f in files), "No image file found"
                
            finally:
                # Cleanup
                await sync_service.stop()
    
    @pytest.mark.asyncio
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
                frame = TextFrame(content="test message")
                frame.metadata = {
                    'chat_id': 123,
                    'thread_id': 456,
                    'chat_title': 'Test Chat'
                }
                
                # Process frame
                await processor.process_frame(frame)
                
                # Mock push failure then success using side_effect
                with patch('git.remote.Remote.push', side_effect=[
                    git.exc.GitCommandError(['git', 'push'], 128, "Network error"),
                    None
                ]):
                    # Wait for sync attempts
                    await asyncio.sleep(3)
                    
                    # Verify git repository state
                    repo = git.Repo(str(storage_path))
                    commits = list(repo.iter_commits())
                    assert any("Added message to topic" in c.message for c in commits)
                    
                    # Verify message file exists and is tracked
                    message_file = next(
                        f for f in repo.tree().traverse()
                        if f.path.endswith('messages.jsonl')
                    )
                    assert message_file.path.startswith("topics/")
            
            finally:
                # Cleanup
                await sync_service.stop()