"""Command handlers for Chronicler bot."""
from typing import Optional
from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.exceptions import CommandError, CommandValidationError, CommandStorageError
from chronicler.logging import get_logger

logger = get_logger(__name__)

async def handle_start(frame: Frame, coordinator: StorageCoordinator) -> Optional[Frame]:
    """Handle /start command."""
    try:
        logger.debug("HANDLER - Processing /start command")
        chat_id = frame.metadata.get("chat_id")
        
        # Check if already initialized
        if await coordinator.is_initialized():
            raise CommandValidationError("Storage is already initialized. Use /status to check current configuration.")
        
        # Initialize storage
        await coordinator.init_storage(chat_id)
        await coordinator.create_topic(chat_id, "default")
        
        return TextFrame(
            content="Storage initialized successfully!",
            metadata=frame.metadata
        )
    except Exception as e:
        logger.error(f"HANDLER - Error handling /start command: {str(e)}")
        if isinstance(e, CommandError):
            raise
        raise CommandError(f"Failed to initialize: {str(e)}")

async def handle_config(frame: Frame, coordinator: StorageCoordinator) -> Optional[Frame]:
    """Handle /config command."""
    try:
        logger.debug("HANDLER - Processing /config command")
        chat_id = frame.metadata.get("chat_id")
        
        # Check if initialized
        if not await coordinator.is_initialized():
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
        await coordinator.set_github_config(token=token, repo=repo)
        await coordinator.sync()
        
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

async def handle_status(frame: Frame, coordinator: StorageCoordinator) -> Optional[Frame]:
    """Handle /status command."""
    try:
        logger.debug("HANDLER - Processing /status command")
        chat_id = frame.metadata.get("chat_id")
        
        # Check initialization status
        initialized = await coordinator.is_initialized()
        if not initialized:
            raise CommandValidationError("Storage not initialized")
        
        # Sync and get repository status
        await coordinator.sync()
        
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