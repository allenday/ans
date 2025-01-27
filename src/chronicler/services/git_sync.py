from pathlib import Path
from git import Repo
from chronicler.logging import get_logger, trace_operation

logger = get_logger(__name__)

class GitSync:
    """Service for managing Git remote synchronization."""
    
    def __init__(self, repo_path: str | Path):
        """Initialize GitSync service.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path)
        self.logger = logger.getChild(self.__class__.__name__)
        self.repo = Repo(self.repo_path)
        
    @trace_operation('services.git_sync')
    async def configure_remote(self, token: str, repo: str) -> None:
        """Configure GitHub remote with token."""
        try:
            # Remove existing remote if it exists
            if 'origin' in [r.name for r in self.repo.remotes]:
                self.repo.delete_remote('origin')

            # Clean up repo URL if needed
            if repo.startswith('https://github.com/'):
                repo = repo[len('https://github.com/'):]
            if repo.endswith('.git'):
                repo = repo[:-4]

            # Configure credential helper to use environment variable
            self.repo.git.config('credential.helper', 
                '!f() { echo username=oauth2; echo "password=$GIT_TOKEN"; }; f')
            
            # Create new remote with HTTPS URL (no credentials)
            self.repo.create_remote('origin', f'https://github.com/{repo}.git')

        except Exception as e:
            logger.error(f"Failed to configure GitHub remote: {e}")
            raise RuntimeError(f"Failed to configure GitHub remote: {e}")
            
    @trace_operation('services.git_sync')
    async def sync(self) -> None:
        """Sync changes with remote repository."""
        try:
            # Check if there are any remotes
            if not list(self.repo.remotes):
                raise RuntimeError("No remotes configured")

            origin = self.repo.remotes['origin']

            # Configure Git to use rebase for pulls
            self.repo.git.config('pull.rebase', 'true')

            # Fetch from remote
            origin.fetch()

            # Pull changes from remote
            self.repo.git.pull('origin', 'main')

            # Push to remote and set up tracking
            self.repo.git.push('--set-upstream', 'origin', 'main')

        except Exception as e:
            logger.error(f"Failed to sync changes: {e}")
            raise RuntimeError(f"Failed to sync changes: {e}") 