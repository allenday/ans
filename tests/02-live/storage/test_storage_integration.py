"""Live tests for storage processor with git integration."""
import pytest
import pytest_asyncio
import os
import git
import asyncio
from pathlib import Path
from chronicler.storage.interface import User
from chronicler.storage.git import GitStorageAdapter
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.services.git_sync_service import GitSyncService
from chronicler.frames import TextFrame, ImageFrame, DocumentFrame

@pytest.fixture
def storage_path(tmp_path):
    """Create a temporary storage path."""
    path = tmp_path / "storage"
    path.mkdir(parents=True, exist_ok=True)
    return path

@pytest.fixture
def git_config():
    """Git configuration for testing."""
    # Get required environment variables
    repo_url = os.environ.get('GIT_REPO_URL')
    branch = os.environ.get('GIT_BRANCH', 'main')
    username = os.environ.get('GIT_USERNAME')
    access_token = os.environ.get('GIT_ACCESS_TOKEN')
    
    if not all([repo_url, username, access_token]):
        pytest.skip("Git environment variables not configured")
    
    return {
        'GIT_REPO_URL': repo_url,
        'GIT_BRANCH': branch,
        'GIT_USERNAME': username,
        'GIT_ACCESS_TOKEN': access_token,
        'GIT_SYNC_INTERVAL': '1'  # 1 second for faster testing
    }

@pytest_asyncio.fixture
async def processor(storage_path, git_config):
    """Create a storage processor with live git integration."""
    # Set up environment
    os.environ.update(git_config)
    
    # Initialize storage adapter
    storage = GitStorageAdapter(storage_path)
    user = User(id="test_user", name="Test User")
    await storage.init_storage(user)
    
    # Create processor
    processor = StorageProcessor(storage_path=storage_path)
    await processor.start()
    
    yield processor
    
    # Cleanup
    await processor.stop()

@pytest.mark.live
class TestLiveStorageIntegration:
    """Live integration tests for storage processor with git integration."""
    
    @pytest.mark.asyncio
    async def test_bidirectional_messages(self, processor):
        """Test handling of sent and received messages with live GitHub sync."""
        # Test SENT message
        sent_frame = TextFrame(content="Hello from user")
        sent_frame.metadata = {
            'chat_id': '123',
            'direction': 'outgoing',
            'is_from_bot': False,
            'thread_id': '456',
            'chat_title': 'Test Chat'
        }
        await processor.process_frame(sent_frame)
        
        # Test RECEIVED message
        received_frame = TextFrame(content="Hello from bot")
        received_frame.metadata = {
            'chat_id': '123',
            'direction': 'incoming',
            'is_from_bot': True,
            'thread_id': '456',
            'chat_title': 'Test Chat'
        }
        await processor.process_frame(received_frame)
        
        # Wait for sync
        await asyncio.sleep(2)
        
        # Verify git repository state
        repo = git.Repo(str(processor.storage_path))
        
        # Check commits
        commits = list(repo.iter_commits())
        assert any("Added message to topic" in c.message for c in commits)
        assert any("456" in c.message for c in commits)
        
        # Verify files exist and are tracked
        files = [item.path for item in repo.tree().traverse()]
        assert any(f.startswith("telegram/") for f in files), "No telegram files found"
        assert any("messages.jsonl" in f for f in files), "No messages file found"
    
    @pytest.mark.asyncio
    async def test_media_attachments(self, processor):
        """Test handling of media attachments with live GitHub sync."""
        # Create and process an image frame
        frame = ImageFrame(
            content=b"test_image_data",
            size=(100, 100),
            format="jpg"
        )
        frame.metadata = {
            'chat_id': '123',
            'thread_id': '456',
            'chat_title': 'Test Chat',
            'file_id': 'test_image'
        }
        
        # Process frame
        await processor.process_frame(frame)
        
        # Wait for sync
        await asyncio.sleep(2)
        
        # Verify git repository state
        repo = git.Repo(str(processor.storage_path))
        
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
    
    @pytest.mark.asyncio
    async def test_git_sync_service(self, processor):
        """Test GitSyncService with live GitHub repository."""
        # Create and process multiple frames
        frames = [
            TextFrame(content=f"Message {i}")
            for i in range(3)
        ]
        for frame in frames:
            frame.metadata = {
                'chat_id': '123',
                'thread_id': '456',
                'chat_title': 'Test Chat'
            }
            await processor.process_frame(frame)
        
        # Wait for sync
        await asyncio.sleep(2)
        
        # Verify git repository state
        repo = git.Repo(str(processor.storage_path))
        
        # Check commits
        commits = list(repo.iter_commits())
        assert any("Added message to topic" in c.message for c in commits)
        assert any("456" in c.message for c in commits)
        
        # Verify files exist and are tracked
        files = [item.path for item in repo.tree().traverse()]
        assert any(f.startswith("telegram/") for f in files), "No telegram files found"
        assert any("messages.jsonl" in f for f in files), "No messages file found" 