"""Command handlers for Chronicler bot."""
from chronicler.logging import get_logger
from abc import ABC, abstractmethod
from typing import Optional

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame
from chronicler.exceptions import (
    CommandError,
    CommandValidationError,
    CommandStorageError,
    CommandAuthorizationError
)

logger = get_logger(__name__)

class CommandHandler(ABC):
    """Base class for command handlers."""
    
    def __init__(self):
        """Initialize command handler."""
        logger.debug(f"HANDLER - Initialized {self.__class__.__name__}")
        
    @abstractmethod
    async def handle(self, frame: Frame) -> Optional[Frame]:
        """Handle a command frame."""
        pass

class StartCommandHandler(CommandHandler):
    """Handler for /start command."""
    
    def __init__(self, coordinator):
        """Initialize start command handler."""
        super().__init__()
        self.coordinator = coordinator
        self.command = "/start"
        
    async def handle(self, frame: Frame) -> Optional[Frame]:
        """Handle /start command."""
        try:
            logger.debug("HANDLER - Processing /start command")
            metadata = frame.get_metadata() if hasattr(frame, 'get_metadata') else frame.metadata
            chat_id = metadata.chat_id if hasattr(metadata, 'chat_id') else metadata.get('chat_id')
            
            # Check if already initialized
            if await self.coordinator.is_initialized():
                raise CommandValidationError("Storage is already initialized. Use /status to check current configuration.")
            
            # Initialize storage
            try:
                await self.coordinator.init_storage(chat_id)
                logger.info(f"HANDLER - Storage initialized for user {chat_id}")
            except Exception as e:
                raise CommandStorageError(f"Failed to initialize storage: {str(e)}")
            
            # Create default topic
            try:
                await self.coordinator.create_topic(chat_id, "default")
                logger.info(f"HANDLER - Created default topic for user {chat_id}")
            except Exception as e:
                raise CommandStorageError(f"Failed to create topic: {str(e)}")
            
            return TextFrame(
                content="Storage initialized successfully! You can now configure your GitHub repository with /config.",
                metadata=metadata if isinstance(metadata, dict) else metadata.__dict__
            )
        except Exception as e:
            logger.error(f"HANDLER - Error handling /start command: {str(e)}")
            if isinstance(e, CommandError):
                raise
            raise CommandError(f"Failed to initialize: {str(e)}")

class ConfigCommandHandler(CommandHandler):
    """Handler for /config command."""
    
    def __init__(self, coordinator):
        """Initialize config command handler."""
        super().__init__()
        self.coordinator = coordinator
        self.command = "/config"
        
    async def handle(self, frame: Frame) -> Optional[Frame]:
        """Handle /config command."""
        try:
            logger.debug("HANDLER - Processing /config command")
            chat_id = frame.metadata.get("chat_id")
            
            # Check if initialized
            if not await self.coordinator.is_initialized():
                raise CommandValidationError("Storage not initialized")
            
            # Validate arguments
            if len(frame.args) != 2:
                raise CommandValidationError("Missing required arguments")
            
            repo, token = frame.args
            
            # Validate repository format
            if not repo or '/' not in repo:
                raise CommandValidationError("Repository must be in format 'username/repository'")
            
            # Validate token format
            if not token or not token.startswith(('ghp_', 'github_pat_')):
                raise CommandValidationError(
                    "Token must be a GitHub Personal Access Token "
                    "(starts with 'ghp_' or 'github_pat_')"
                )
            
            # Configure GitHub repository
            try:
                await self.coordinator.set_github_config(token=token, repo=repo)
                logger.info(f"HANDLER - GitHub configuration set for user {chat_id}")
            except Exception as e:
                raise CommandStorageError(f"Failed to configure GitHub: {str(e)}")
            
            # Try to sync to verify credentials
            try:
                await self.coordinator.sync()
                logger.info(f"HANDLER - Successfully synced repository for user {chat_id}")
            except Exception as e:
                raise CommandStorageError(f"Failed to sync repository: {str(e)}")
            
            return TextFrame(
                content=(
                    "GitHub configuration updated!\n\n"
                    f"I'll now archive your messages to:\n"
                    f"https://github.com/{repo}\n\n"
                    "You can check the current status with /status"
                ),
                metadata=frame.metadata
            )
        except Exception as e:
            logger.error(f"HANDLER - Error handling /config command: {str(e)}")
            if isinstance(e, CommandError):
                raise
            raise CommandError(f"Failed to configure: {str(e)}")

class StatusCommandHandler(CommandHandler):
    """Handler for /status command."""
    
    def __init__(self, coordinator):
        """Initialize status command handler."""
        super().__init__()
        self.coordinator = coordinator
        self.command = "/status"
        
    async def handle(self, frame: Frame) -> Optional[Frame]:
        """Handle /status command."""
        try:
            logger.debug("HANDLER - Processing /status command")
            chat_id = frame.metadata.get("chat_id")
            
            # Check initialization status
            try:
                initialized = await self.coordinator.is_initialized()
                logger.debug(f"HANDLER - Storage initialized status for user {chat_id}: {initialized}")
            except Exception as e:
                raise CommandStorageError(f"Failed to check initialization status: {str(e)}")
            
            if not initialized:
                logger.warning(f"HANDLER - Storage not initialized for user {chat_id}")
                raise CommandValidationError("Storage not initialized")
            
            # Sync and get repository status
            try:
                await self.coordinator.sync()
                logger.info(f"HANDLER - Successfully synced repository for user {chat_id}")
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
            logger.error(f"HANDLER - Error handling /status command: {str(e)}")
            if isinstance(e, CommandError):
                raise
            raise CommandError(f"Failed to get status: {str(e)}") 