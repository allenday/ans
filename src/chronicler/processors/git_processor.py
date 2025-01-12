"""Git processor implementation."""
import os
import logging
import threading
from pathlib import Path
import git
from git.exc import GitCommandError

class GitProcessingError(Exception):
    """Git processing error."""

class GitProcessor:
    """Git processor implementation."""

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

        Raises:
            GitProcessingError: If any required parameters are invalid
        """
        # Validate parameters
        if not repo_url:
            raise GitProcessingError("Repository URL is required")
        if not branch:
            raise GitProcessingError("Branch name is required")
        if not username:
            raise GitProcessingError("Username is required")
        if not access_token:
            raise GitProcessingError("Access token is required")
        if not storage_path:
            raise GitProcessingError("Storage path is required")

        self.repo_url = repo_url
        self.branch = branch
        self.username = username
        self.access_token = access_token
        self.storage_path = Path(storage_path)
        self._git_lock = threading.Lock()
        self._logger = logging.getLogger(__name__)

        # Initialize repo
        try:
            self._repo = git.Repo(str(storage_path))
            self._logger.info(f"Using existing git repository at {storage_path}")
        except git.exc.InvalidGitRepositoryError:
            self._logger.info(f"Initializing new git repository at {storage_path}")
            self._repo = git.Repo.init(str(storage_path))
            # Configure Git user for commits
            with self._repo.config_writer() as git_config:
                git_config.set_value('user', 'name', username)
                git_config.set_value('user', 'email', f"{username}@users.noreply.github.com")
            # Create initial commit
            readme_path = self.storage_path / "README.md"
            readme_path.write_text("# Chronicler Archive\n\nThis repository contains archived Telegram messages and media.")
            self._repo.index.add([str(readme_path.relative_to(self.storage_path))])
            self._repo.index.commit("Initial commit")

        self._setup_remote()

    def _setup_remote(self):
        """Set up remote repository."""
        # Add remote if it doesn't exist
        try:
            origin = self._repo.remote("origin")
            origin.set_url(self._get_remote_url())
        except ValueError:
            self._logger.info("Adding remote 'origin'")
            self._repo.create_remote("origin", self._get_remote_url())

        # Create and checkout branch
        if self.branch not in self._repo.heads:
            self._logger.info(f"Creating branch {self.branch}")
            self._repo.create_head(self.branch)

        self._logger.info(f"Checking out branch {self.branch}")
        self._repo.heads[self.branch].checkout()

        # Set up tracking
        try:
            self._logger.info(f"Setting up tracking for branch {self.branch}")
            self._repo.heads[self.branch].set_tracking_branch(
                self._repo.remote("origin").refs[self.branch]
            )
        except (IndexError, GitCommandError) as e:
            self._logger.warning(
                f"Could not set up tracking for branch {self.branch} "
                f"- remote branch may not exist yet: {str(e)}"
            )

    def _get_remote_url(self) -> str:
        """Get remote URL with authentication."""
        # Insert authentication into URL
        # Example: https://username:token@github.com/owner/repo.git
        parts = self.repo_url.split("://", 1)
        if len(parts) != 2:
            raise GitProcessingError(f"Invalid repository URL: {self.repo_url}")
        return f"{parts[0]}://{self.username}:{self.access_token}@{parts[1]}"

    def commit_message(self, message_path: Path):
        """Commit message file.

        Args:
            message_path: Path to message file

        Raises:
            GitProcessingError: If commit fails
        """
        # Validate path
        if not message_path.is_relative_to(self.storage_path):
            raise GitProcessingError(
                f"Message path {message_path} is outside storage directory"
            )
        if not message_path.exists():
            raise GitProcessingError(f"Message path {message_path} does not exist")

        # Add and commit file
        with self._git_lock:
            try:
                self._repo.index.add([
                    str(message_path.relative_to(self.storage_path))
                ])
                self._repo.index.commit(f"Add message {message_path.name}")
            except GitCommandError as e:
                raise GitProcessingError(f"Failed to commit message: {str(e)}")

    def commit_media(self, media_paths: list[Path]):
        """Commit media files.

        Args:
            media_paths: List of paths to media files

        Raises:
            GitProcessingError: If commit fails
        """
        if not media_paths:
            raise GitProcessingError("No media paths provided")

        # Validate paths
        for path in media_paths:
            if not path.is_relative_to(self.storage_path):
                raise GitProcessingError(
                    f"Media path {path} is outside storage directory"
                )
            if not path.exists():
                raise GitProcessingError(f"Media path {path} does not exist")

        # Add and commit files
        with self._git_lock:
            try:
                self._repo.index.add([
                    str(path.relative_to(self.storage_path))
                    for path in media_paths
                ])
                self._repo.index.commit(
                    f"Add {len(media_paths)} media files"
                )
            except GitCommandError as e:
                raise GitProcessingError(f"Failed to commit media: {str(e)}")

    def push_changes(self):
        """Push changes to remote repository.

        Raises:
            GitProcessingError: If push fails
        """
        if not self.repo_url:
            raise GitProcessingError("Repository URL not configured")

        with self._git_lock:
            try:
                self._repo.remotes.origin.push(self.branch)
                self._logger.info("Successfully pushed changes to remote")
            except GitCommandError as e:
                self._logger.error("Failed to push changes")
                raise GitProcessingError(
                    f"Failed to push changes to remote: {str(e)}"
                )