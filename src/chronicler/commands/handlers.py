"""Command handlers for Chronicler bot."""
from chronicler.logging import get_logger, trace_operation
from abc import ABC, abstractmethod
from typing import Optional

from chronicler.commands.frames import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.storage.interface import User

logger = get_logger(__name__)

class CommandHandler(ABC):
    """Base class for command handlers."""
    
    def __init__(self, coordinator: StorageCoordinator):
        """Initialize command handler."""
        self.coordinator = coordinator
        logger.debug(f"HANDLER - Initialized {self.__class__.__name__}")
        
    @abstractmethod
    @trace_operation('commands.handler')
    async def handle(self, frame: CommandFrame) -> TextFrame:
        """Handle a command frame."""
        pass

class StartCommandHandler(CommandHandler):
    """Handler for /start command."""
    
    @trace_operation('commands.handler.start')
    async def handle(self, frame: CommandFrame) -> TextFrame:
        """Initialize bot configuration for a user."""
        user_id = frame.metadata['sender_id']
        user_name = frame.metadata['sender_name']
        logger.info(f"HANDLER - Processing /start command for user {user_name} (ID: {user_id})")
        
        try:
            # Create user object
            user = User(
                id=str(user_id),
                name=user_name,
                metadata=frame.metadata
            )
            logger.debug(f"HANDLER - Created User object for {user_name}")
            
            # Initialize storage
            await self.coordinator.init_storage(user)
            logger.info(f"HANDLER - Storage initialized for user {user.id}")
            
            # Create default topic
            await self.coordinator.create_topic("default", frame.metadata)
            logger.info(f"HANDLER - Created default topic for user {user.id}")
            
            return TextFrame(
                text=(
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
            raise

class ConfigCommandHandler(CommandHandler):
    """Handler for /config command."""
    
    @trace_operation('commands.handler.config')
    async def handle(self, frame: CommandFrame) -> TextFrame:
        """Configure Git repository settings."""
        user_id = frame.metadata['sender_id']
        user_name = frame.metadata['sender_name']
        logger.info(f"HANDLER - Processing /config command for user {user_name} (ID: {user_id})")
        
        # Check for required arguments (repo and token)
        if len(frame.args) < 2:
            logger.warning(f"HANDLER - Invalid number of arguments for /config command from user {user_id}")
            return TextFrame(
                text=(
                    "Usage: /config <github_repo> <token>\n\n"
                    "Example:\n"
                    "/config username/repo ghp_1234567890abcdef"
                ),
                metadata=frame.metadata
            )
            
        # Take first argument as repo and second as token
        repo, token = frame.args[0], frame.args[1]
        logger.debug(f"HANDLER - Configuring repository {repo} for user {user_id}")
        
        try:
            # Configure GitHub repository
            await self.coordinator.set_github_config(token=token, repo=repo)
            logger.info(f"HANDLER - GitHub configuration set for user {user_id}")
            
            # Try to sync to verify credentials
            await self.coordinator.sync()
            logger.info(f"HANDLER - Successfully synced repository for user {user_id}")
            
            return TextFrame(
                text=(
                    "GitHub configuration updated!\n\n"
                    "I'll now archive your messages to:\n"
                    f"https://github.com/{repo}\n\n"
                    "You can check the current status with /status"
                ),
                metadata=frame.metadata
            )
            
        except Exception as e:
            logger.error(f"HANDLER - Failed to configure repository for user {user_id}: {e}", exc_info=True)
            raise

class StatusCommandHandler(CommandHandler):
    """Handler for /status command."""
    
    @trace_operation('commands.handler.status')
    async def handle(self, frame: CommandFrame) -> TextFrame:
        """Show current settings and state."""
        user_id = frame.metadata['sender_id']
        user_name = frame.metadata['sender_name']
        logger.info(f"HANDLER - Processing /status command for user {user_name} (ID: {user_id})")
        
        try:
            initialized = await self.coordinator.is_initialized()
            logger.debug(f"HANDLER - Storage initialized status for user {user_id}: {initialized}")
            
            if not initialized:
                logger.warning(f"HANDLER - Storage not initialized for user {user_id}")
                return TextFrame(
                    text="Storage not initialized. Please use /start first.",
                    metadata=frame.metadata
                )
            
            # Sync to get latest state
            await self.coordinator.sync()
            logger.info(f"HANDLER - Successfully synced repository for user {user_id}")
            
            return TextFrame(
                text=(
                    "Chronicler Status:\n"
                    "- Storage: Initialized\n"
                    "- GitHub: Connected\n"
                    "- Last sync: Success"
                ),
                metadata=frame.metadata
            )
            
        except Exception as e:
            logger.error(f"HANDLER - Failed to get status for user {user_id}: {e}", exc_info=True)
            raise 