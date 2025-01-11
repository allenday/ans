import logging
from pathlib import Path
from typing import List, Optional
import git
from git.exc import GitError

logger = logging.getLogger(__name__)

class GitProcessingError(Exception):
    """Raised when git operations fail."""
    pass

class GitProcessor:
    """Handles git operations for message archival."""
    
    def __init__(
        self,
        repo_url: str,
        branch: str,
        username: str,
        access_token: str,
        storage_path: Path
    ):
        """Initialize GitProcessor.
        
        Args:
            repo_url: URL of the git repository
            branch: Branch to commit to
            username: Git username for authentication
            access_token: Git access token for authentication
            storage_path: Path to the storage directory
        """
        self.repo_url = repo_url
        self.branch = branch
        self.username = username
        self.access_token = access_token
        self.storage_path = Path(storage_path)
        
        # Initialize repo
        try:
            self._repo = git.Repo(str(storage_path))
            logger.info("Using existing git repository at %s", storage_path)
        except (git.NoSuchPathError, git.InvalidGitRepositoryError):
            logger.info("Initializing new git repository at %s", storage_path)
            self._repo = git.Repo.init(str(storage_path))
            self._setup_remote()
    
    def _setup_remote(self):
        """Configure the remote repository."""
        auth_url = self.repo_url.replace(
            "https://",
            f"https://{self.username}:{self.access_token}@"
        )
        
        try:
            if "origin" in self._repo.remotes:
                self._repo.delete_remote("origin")
            self._repo.create_remote("origin", auth_url)
            logger.info("Configured remote repository")
        except GitError as e:
            logger.error("Failed to configure remote", exc_info=True)
            raise GitProcessingError("Failed to configure remote repository") from e
    
    def commit_message(self, message_path: Path) -> None:
        """Commit a message file to the repository.
        
        Args:
            message_path: Path to the message file
        """
        try:
            rel_path = message_path.relative_to(self.storage_path)
            self._repo.index.add([str(message_path)])
            self._repo.index.commit(f"Add message: {rel_path}")
            logger.info("Committed message file: %s", rel_path)
        except Exception as e:
            logger.error("Failed to commit message", exc_info=True)
            raise GitProcessingError("Failed to commit message") from e
    
    def commit_media(self, media_paths: List[Path]) -> None:
        """Commit media files to the repository.
        
        Args:
            media_paths: List of paths to media files
        """
        try:
            rel_paths = [p.relative_to(self.storage_path) for p in media_paths]
            self._repo.index.add([str(p) for p in media_paths])
            self._repo.index.commit(
                f"Add media files:\n" + "\n".join(f"- {p}" for p in rel_paths)
            )
            logger.info("Committed %d media files", len(media_paths))
        except Exception as e:
            logger.error("Failed to commit media files", exc_info=True)
            raise GitProcessingError("Failed to commit media files") from e
    
    def push_changes(self) -> None:
        """Push committed changes to the remote repository."""
        try:
            self._repo.remotes.origin.push(self.branch)
            logger.info("Successfully pushed changes to remote")
        except Exception as e:
            logger.error("Failed to push changes", exc_info=True)
            raise GitProcessingError("Failed to push changes to remote") from e 