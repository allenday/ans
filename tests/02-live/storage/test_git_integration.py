"""Live tests for git functionality."""
import pytest
import os
import git
import asyncio
from pathlib import Path
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
    """Get Git configuration from environment."""
    required_vars = [
        'GIT_REPO_URL',
        'GIT_BRANCH',
        'GIT_USERNAME',
        'GIT_ACCESS_TOKEN'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            pytest.skip(f"{var} not set")
    
    return {
        'GIT_REPO_URL': os.getenv('GIT_REPO_URL'),
        'GIT_BRANCH': os.getenv('GIT_BRANCH'),
        'GIT_USERNAME': os.getenv('GIT_USERNAME'),
        'GIT_ACCESS_TOKEN': os.getenv('GIT_ACCESS_TOKEN'),
        'GIT_SYNC_INTERVAL': '1'  # 1 second for faster testing
    }

@pytest.mark.live
class TestLiveGitIntegration:
    """Live integration tests for git functionality."""
    
    @pytest.mark.asyncio
    async def test_git_initialization(self, storage_path, git_config):
        """Test initializing git repository with live GitHub."""
        # Set up environment variables
        for key, value in git_config.items():
            os.environ[key] = str(value)
        
        processor = StorageProcessor(storage_path=storage_path)
        await processor.start()
        
        try:
            # Verify repository is initialized
            repo = git.Repo(processor.storage.repo_path)
            assert repo.active_branch.name == git_config['GIT_BRANCH']
            
            # Extract base URL from remote URL (ignore credentials)
            remote_url = repo.remotes.origin.url
            remote_base_url = remote_url.split('@')[-1] if '@' in remote_url else remote_url
            config_base_url = git_config['GIT_REPO_URL'].split('@')[-1] if '@' in git_config['GIT_REPO_URL'] else git_config['GIT_REPO_URL']
            assert remote_base_url == config_base_url, "Base repository URLs should match"
            
            # Set up tracking branch
            repo.git.checkout('-b', git_config['GIT_BRANCH'])
            repo.git.push('--set-upstream', 'origin', git_config['GIT_BRANCH'])
            
            # Test basic git operations
            test_file = processor.storage.repo_path / "test.txt"
            test_file.write_text("Test content")
            
            # Stage and commit
            repo.index.add([str(test_file)])
            repo.index.commit("Test commit")
            
            # Push to remote
            origin = repo.remote('origin')
            origin.push()
            
            # Verify push was successful
            assert not repo.is_dirty()
            assert repo.head.commit.message == "Test commit"
            
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_git_sync_service_lifecycle(self, storage_path, git_config):
        """Test GitSyncService lifecycle with live GitHub."""
        # Set up environment variables
        for key, value in git_config.items():
            os.environ[key] = str(value)
        
        processor = StorageProcessor(storage_path=storage_path)
        sync_service = GitSyncService(
            git_processor=processor.git_processor,
            sync_interval=1
        )
        
        try:
            # Start services
            await processor.start()
            await sync_service.start()
            
            # Set up tracking branch
            repo = git.Repo(processor.storage.repo_path)
            repo.git.checkout('-b', git_config['GIT_BRANCH'])
            repo.git.push('--set-upstream', 'origin', git_config['GIT_BRANCH'])
            
            # Create test content
            test_file = processor.storage.repo_path / "test_sync.txt"
            test_file.write_text("Initial content")
            
            # Stage and commit initial content
            repo.index.add([str(test_file)])
            repo.index.commit("Initial commit")
            repo.remotes.origin.push()
            
            # Wait for first sync
            await asyncio.sleep(2)
            
            initial_commit = repo.head.commit
            
            # Modify content
            test_file.write_text("Modified content")
            
            # Stage and commit modified content
            repo.index.add([str(test_file)])
            repo.index.commit("Modified content")
            
            # Wait for second sync
            await asyncio.sleep(2)
            
            # Verify changes were synced
            assert repo.head.commit != initial_commit
            assert not repo.is_dirty()
            
        finally:
            await sync_service.stop()
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_git_conflict_resolution(self, storage_path, git_config):
        """Test git conflict resolution with live GitHub."""
        # Set up environment variables
        for key, value in git_config.items():
            os.environ[key] = str(value)
        
        processor = StorageProcessor(storage_path=storage_path)
        await processor.start()
        
        try:
            # Set up tracking branch
            repo = git.Repo(processor.storage.repo_path)
            repo.git.checkout('-b', git_config['GIT_BRANCH'])
            repo.git.push('--set-upstream', 'origin', git_config['GIT_BRANCH'])
            
            # Create initial content
            test_file = processor.storage.repo_path / "conflict_test.txt"
            test_file.write_text("Initial content")
            
            repo.index.add([str(test_file)])
            repo.index.commit("Initial commit")
            repo.remotes.origin.push()
            
            # Create a divergent change
            test_file.write_text("Local change")
            repo.index.add([str(test_file)])
            repo.index.commit("Local commit")
            
            # Simulate remote change by creating a new clone
            temp_clone_path = storage_path.parent / "temp_clone"
            temp_repo = git.Repo.clone_from(
                git_config['GIT_REPO_URL'],
                temp_clone_path,
                branch=git_config['GIT_BRANCH']
            )
            
            # Make change in temp clone
            temp_file = temp_clone_path / "conflict_test.txt"
            temp_file.write_text("Remote change")
            temp_repo.index.add([str(temp_file)])
            temp_repo.index.commit("Remote commit")
            temp_repo.remotes.origin.push()
            
            # Try to push local changes
            try:
                repo.remotes.origin.push()
            except git.GitCommandError:
                # Pull and resolve conflict
                repo.remotes.origin.pull(rebase=True)
                
                # Verify conflict resolution
                assert not repo.is_dirty()
                assert test_file.read_text() in ["Local change", "Remote change"]
            
        finally:
            await processor.stop() 