"""User story for testing GitSync service.

As a user of the GitSync service
I want to initialize a local Git repository and configure it with GitHub
So that I can sync my changes with a remote repository

The story goes:
1. Initialize GitSync service with a local path
2. Configure GitHub remote with token and repository
3. Make some local changes
4. Sync changes with remote repository
"""

import os
import pytest
from pathlib import Path
from git import Repo
from chronicler.services.git_sync import GitSync
import uuid
import shutil
from datetime import datetime
from chronicler.processors.base import BaseProcessor

@pytest.fixture
def test_config():
    """Load test configuration from environment variables."""
    required_vars = [
        'GIT_TOKEN',
        'GITHUB_TEST_REPO',
        'GIT_USER_NAME',
        'GIT_USER_EMAIL'
    ]
    
    config = {}
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            pytest.skip(f'Required environment variable {var} not set')
        config[var] = value
    
    # Set up tmp directory path
    config['GIT_LOCAL_PATH'] = str(Path('tmp') / f'git_sync_test_{uuid.uuid4().hex[:8]}')
    return config

@pytest.fixture
def temp_repo_path(test_config):
    """Create a temporary repository path."""
    path = Path(test_config['GIT_LOCAL_PATH'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir(parents=True, exist_ok=True)
    
    # Initialize git repo if it doesn't exist
    if not (path / '.git').exists():
        repo = Repo.init(path)
        # Set up Git user config for this repo
        with repo.config_writer() as git_config:
            git_config.set_value('user', 'name', test_config['GIT_USER_NAME'])
            git_config.set_value('user', 'email', test_config['GIT_USER_EMAIL'])
        # Create initial commit
        (path / '.gitkeep').touch()
        repo.index.add(['.gitkeep'])
        repo.index.commit('Initial commit')
    else:
        # Clean up any existing test files
        repo = Repo(path)
        for item in path.glob('test_*.txt'):
            item.unlink()
            repo.index.remove([str(item.relative_to(path))])
        if repo.is_dirty():
            repo.index.commit('Clean up test files')
    
    yield path
    
    # Clean up after test
    if path.exists():
        shutil.rmtree(path)

@pytest.fixture
def git_sync(temp_repo_path):
    """Create GitSync service instance."""
    return GitSync(temp_repo_path)

@pytest.mark.asyncio
async def test_git_sync_flow(test_config, git_sync):
    """Test the complete flow of GitSync service."""
    # Configure GitHub remote
    await git_sync.configure_remote(
        token=test_config['GIT_TOKEN'],
        repo=test_config['GITHUB_TEST_REPO']
    )
    
    # Make some local changes with a unique file name
    test_file = Path(git_sync.repo_path) / f'test_{uuid.uuid4().hex[:8]}.txt'
    test_file.write_text('Test content')
    git_sync.repo.index.add([str(test_file.relative_to(git_sync.repo_path))])
    git_sync.repo.index.commit('Add test file')
    
    # Sync changes with remote
    await git_sync.sync()
    
    # Verify remote is configured
    assert 'origin' in git_sync.repo.remotes
    remote_url = git_sync.repo.remotes['origin'].url
    assert test_config['GITHUB_TEST_REPO'] in remote_url
    
    # Verify branch exists and points to the correct remote
    assert git_sync.repo.active_branch.name == 'main'
    assert git_sync.repo.git.config('branch.main.remote') == 'origin'
    assert git_sync.repo.git.config('branch.main.merge') == 'refs/heads/main'

@pytest.mark.asyncio
async def test_git_sync_background_sync(test_config, git_sync):
    """Test GitSync service running in background with pipecat.
    
    This test simulates a background processor that:
    1. Makes no data transformations
    2. Periodically updates a status file
    3. Syncs changes with remote repository
    """
    from chronicler.frames.base import Frame
    import asyncio
    from datetime import datetime
    
    # Configure GitHub remote
    await git_sync.configure_remote(
        token=test_config['GIT_TOKEN'],
        repo=test_config['GITHUB_TEST_REPO']
    )
    
    # Create status file
    status_file = Path(git_sync.repo_path) / 'status.txt'
    status_file.write_text('Pipeline started\n')
    git_sync.repo.index.add([str(status_file.relative_to(git_sync.repo_path))])
    git_sync.repo.index.commit('Initialize status file')
    await git_sync.sync()
    
    # Create a simple background processor that updates status
    class StatusUpdater(BaseProcessor):
        def __init__(self, git_sync, status_file):
            super().__init__()
            self.git_sync = git_sync
            self.status_file = status_file
            self.update_count = 0
        
        async def process(self, frame: Frame = None) -> Frame:
            # Update status file
            self.update_count += 1
            timestamp = datetime.now().isoformat()
            self.status_file.write_text(f'Pipeline running - Update {self.update_count} at {timestamp}\n')
            self.git_sync.repo.index.add([str(self.status_file.relative_to(self.git_sync.repo_path))])
            self.git_sync.repo.index.commit(f'Update status - {self.update_count}')
            await self.git_sync.sync()
            return frame
    
    # Create and run the status updater
    updater = StatusUpdater(git_sync, status_file)
    
    # Run for 3 updates (about 30 seconds)
    for _ in range(3):
        await updater.process()
        await asyncio.sleep(10)
    
    # Verify the changes were synced
    # Pull latest changes to ensure we're up to date
    await git_sync.sync()
    
    # Check status file exists and has content
    assert status_file.exists()
    content = status_file.read_text()
    assert 'Pipeline running - Update 3' in content
    
    # Verify commits were made and pushed
    commits = list(git_sync.repo.iter_commits())
    assert len(commits) >= 4  # Initial + 3 updates
    assert 'Update status - 3' in commits[0].message 