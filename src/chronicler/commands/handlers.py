"""Command handlers for Chronicler bot."""
from chronicler.logging import get_logger, trace_operation
from abc import ABC, abstractmethod
from typing import Optional, Any

from chronicler.commands.frames import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.exceptions import (
    CommandError,
    CommandValidationError,
    CommandStorageError,
    CommandAuthorizationError,
    CommandExecutionError
)

logger = get_logger(__name__)

class CommandHandler(ABC):
    """Base class for command handlers."""
    
    def __init__(self):
        """Initialize command handler."""
        logger.debug(f"HANDLER - Initialized {self.__class__.__name__}")
        
    @abstractmethod
    @trace_operation('commands.handler')
    async def handle(self, frame: CommandFrame) -> TextFrame:
        """Handle a command frame."""
        pass

class StorageAwareHandler(CommandHandler):
    """Base class for handlers that need storage access."""
    
    def __init__(self, storage_coordinator: Any):
        """Initialize storage-aware handler.
        
        Args:
            storage_coordinator: The storage coordinator instance
        """
        super().__init__()
        self.storage = storage_coordinator
        logger.debug(f"HANDLER - Initialized storage-aware handler {self.__class__.__name__}")

class StartCommandHandler(StorageAwareHandler):
    """Handler for /start command."""
    
    @trace_operation('commands.handler.start')
    async def handle(self, frame: CommandFrame) -> TextFrame:
        """Initialize bot configuration for a user."""
        user_id = frame.metadata['sender_id']
        user_name = frame.metadata['sender_name']
        logger.info(f"HANDLER - Processing /start command for user {user_name} (ID: {user_id})")
        
        try:
            # Check if already initialized
            initialized = await self.storage.is_initialized()
            if initialized:
                raise CommandValidationError("Storage is already initialized. Use /status to check current configuration.")
            
            # Initialize storage
            try:
                await self.storage.init_storage(user_id)
                logger.info(f"HANDLER - Storage initialized for user {user_id}")
            except Exception as e:
                raise CommandStorageError(f"Failed to initialize storage: {str(e)}")
            
            # Create default topic
            try:
                await self.storage.create_topic("default", frame.metadata)
                logger.info(f"HANDLER - Created default topic for user {user_id}")
            except Exception as e:
                raise CommandStorageError(f"Failed to create default topic: {str(e)}")
            
            return TextFrame(
                content=(
                    "Welcome to Chronicler! 🤖\n\n"
                    "I'll help you archive your Telegram messages in a Git repository.\n\n"
                    "To get started, configure your repository with:\n"
                    "/config <github_repo> <token>\n\n"
                    "Example:\n"
                    "/config username/repo ghp_1234567890abcdef"
                ),
                metadata=frame.metadata
            )
            
        except Exception as e:
            logger.error(f"HANDLER - Failed to handle /start command for user {user_id}: {e}", exc_info=True)
            if isinstance(e, CommandError):
                raise
            raise CommandExecutionError(f"Failed to initialize: {str(e)}")

class ConfigCommandHandler(StorageAwareHandler):
    """Handler for /config command."""
    
    def _validate_repo_format(self, repo: str) -> None:
        """Validate repository format.
        
        Args:
            repo: Repository string to validate
            
        Raises:
            CommandValidationError: If format is invalid
        """
        if not repo or '/' not in repo:
            raise CommandValidationError(
                "Repository must be in format 'username/repository'"
            )
        username, reponame = repo.split('/', 1)
        if not username or not reponame:
            raise CommandValidationError(
                "Both username and repository name must be provided"
            )
            
    def _validate_token_format(self, token: str) -> None:
        """Validate token format.
        
        Args:
            token: Token string to validate
            
        Raises:
            CommandValidationError: If format is invalid
        """
        if not token:
            raise CommandValidationError("Token cannot be empty")
        if not token.startswith(('ghp_', 'github_pat_')):
            raise CommandValidationError(
                "Token must be a GitHub Personal Access Token (starts with 'ghp_' or 'github_pat_')"
            )
    
    @trace_operation('commands.handler.config')
    async def handle(self, frame: CommandFrame) -> TextFrame:
        """Configure Git repository settings."""
        user_id = frame.metadata['sender_id']
        user_name = frame.metadata['sender_name']
        logger.info(f"HANDLER - Processing /config command for user {user_name} (ID: {user_id})")
        
        # Check for required arguments (repo and token)
        if len(frame.args) < 2:
            raise CommandValidationError(
                "Usage: /config <github_repo> <token>\n\n"
                "Example:\n"
                "/config username/repo ghp_1234567890abcdef"
            )
            
        # Take first argument as repo and second as token
        repo, token = frame.args[0], frame.args[1]
        
        # Validate inputs
        self._validate_repo_format(repo)
        self._validate_token_format(token)
        
        logger.debug(f"HANDLER - Configuring repository {repo} for user {user_id}")
        
        try:
            # Configure GitHub repository
            await self.storage.set_github_config(token=token, repo=repo)
            logger.info(f"HANDLER - GitHub configuration set for user {user_id}")
            
            # Try to sync to verify credentials
            try:
                await self.storage.sync()
                logger.info(f"HANDLER - Successfully synced repository for user {user_id}")
            except Exception as e:
                raise CommandStorageError(f"Failed to sync repository: {str(e)}")
            
            return TextFrame(
                content=(
                    "GitHub configuration updated!\n\n"
                    "I'll now archive your messages to:\n"
                    f"https://github.com/{repo}\n\n"
                    "You can check the current status with /status"
                ),
                metadata=frame.metadata
            )
            
        except Exception as e:
            logger.error(f"HANDLER - Failed to configure repository for user {user_id}: {e}", exc_info=True)
            if isinstance(e, CommandError):
                raise
            raise CommandExecutionError(f"Failed to configure repository: {str(e)}")

class StatusCommandHandler(StorageAwareHandler):
    """Handler for /status command."""
    
    @trace_operation('commands.handler.status')
    async def handle(self, frame: CommandFrame) -> TextFrame:
        """Show current settings and state."""
        user_id = frame.metadata['sender_id']
        user_name = frame.metadata['sender_name']
        logger.info(f"HANDLER - Processing /status command for user {user_name} (ID: {user_id})")
        
        try:
            # Check initialization status
            try:
                initialized = await self.storage.is_initialized()
                logger.debug(f"HANDLER - Storage initialized status for user {user_id}: {initialized}")
            except Exception as e:
                raise CommandStorageError(f"Failed to check initialization status: {str(e)}")
            
            if not initialized:
                logger.warning(f"HANDLER - Storage not initialized for user {user_id}")
                raise CommandValidationError("Storage not initialized. Please use /start first.")
            
            # Sync and get repository status
            try:
                await self.storage.sync()
                logger.info(f"HANDLER - Successfully synced repository for user {user_id}")
            except Exception as e:
                raise CommandStorageError(f"Failed to sync repository: {str(e)}")
            
            return TextFrame(
                content=(
                    "Chronicler Status:\n"
                    "- Storage: Initialized\n"
                    "- GitHub: Connected\n"
                    "- Last sync: Success"
                ),
                metadata=frame.metadata
            )
            
        except Exception as e:
            logger.error(f"HANDLER - Failed to get status for user {user_id}: {e}", exc_info=True)
            if isinstance(e, CommandError):
                raise
            raise CommandExecutionError(f"Failed to get status: {str(e)}") 