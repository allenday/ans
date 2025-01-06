"""Command handlers for Chronicler bot."""
import logging
from abc import ABC, abstractmethod
from typing import Optional

from chronicler.commands.frames import CommandFrame
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.storage.interface import User

logger = logging.getLogger(__name__)

class CommandHandler(ABC):
    """Base class for command handlers."""
    
    def __init__(self, storage: StorageCoordinator):
        self.storage = storage
        
    @abstractmethod
    async def handle(self, frame: CommandFrame) -> str:
        """Handle a command frame."""
        pass

class StartCommandHandler(CommandHandler):
    """Handler for /start command."""
    
    async def handle(self, frame: CommandFrame) -> str:
        """Initialize bot configuration for a user."""
        logger.info(f"Handling /start command for user {frame.metadata['sender_id']}")
        
        try:
            # Create user object
            user = User(
                id=frame.metadata['sender_id'],
                name=frame.metadata['sender_name'],
                metadata=frame.metadata
            )
            
            # Initialize storage
            await self.storage.init_storage(user)
            logger.info(f"Storage initialized for user {user.id}")
            
            return (
                "Welcome to Chronicler! 🤖\n\n"
                "I'll help you archive your Telegram messages in a Git repository.\n\n"
                "To get started, configure your repository with:\n"
                "/config <github_repo> <token>\n\n"
                "Example:\n"
                "/config username/repo ghp_1234567890abcdef"
            )
            
        except Exception as e:
            logger.error(f"Failed to handle /start command: {e}", exc_info=True)
            raise

class ConfigCommandHandler(CommandHandler):
    """Handler for /config command."""
    
    async def handle(self, frame: CommandFrame) -> str:
        """Configure Git repository settings."""
        logger.info(f"Handling /config command for user {frame.metadata['sender_id']}")
        
        if len(frame.args) != 2:
            logger.warning("Invalid number of arguments for /config command")
            return (
                "❌ Invalid configuration format.\n\n"
                "Usage:\n"
                "/config <github_repo> <token>\n\n"
                "Example:\n"
                "/config username/repo ghp_1234567890abcdef"
            )
            
        repo, token = frame.args
        
        try:
            # Configure GitHub repository
            await self.storage.set_github_config(token, repo)
            logger.info("GitHub configuration set successfully")
            
            # Try to sync to verify credentials
            await self.storage.sync()
            logger.info("Successfully synced with remote repository")
            
            return (
                "✅ Repository configured successfully!\n\n"
                "I'll now archive your messages to:\n"
                f"https://github.com/{repo}\n\n"
                "You can check the current status with /status"
            )
            
        except Exception as e:
            logger.error(f"Failed to configure repository: {e}", exc_info=True)
            return (
                "❌ Failed to configure repository.\n\n"
                "Please check:\n"
                "- Repository exists and is accessible\n"
                "- Token has correct permissions\n"
                "- Repository name is in format username/repo"
            )

class StatusCommandHandler(CommandHandler):
    """Handler for /status command."""
    
    async def handle(self, frame: CommandFrame) -> str:
        """Show current settings and state."""
        logger.info(f"Handling /status command for user {frame.metadata['sender_id']}")
        
        try:
            # Get metadata from storage
            metadata_path = self.storage.repo_path / "metadata.yaml"
            if not metadata_path.exists():
                logger.warning("No metadata file found")
                return (
                    "❌ Bot not initialized.\n\n"
                    "Please use /start to initialize the bot first."
                )
            
            with open(metadata_path) as f:
                import yaml
                metadata = yaml.safe_load(f)
            
            # Format status message
            status = ["📊 Current Status"]
            
            # User info
            user = metadata.get('user', {})
            status.append(f"\n👤 User: {user.get('name')} (ID: {user.get('id')})")
            
            # GitHub config
            github = metadata.get('github', {})
            if github:
                status.append(f"\n📦 Repository: {github.get('repo')}")
                status.append("🔗 Connection: Active")
            else:
                status.append("\n⚠️ No repository configured")
                status.append("Use /config to set up your repository")
            
            # Add statistics if available
            if 'stats' in metadata:
                stats = metadata['stats']
                status.append(f"\n📈 Statistics:")
                status.append(f"- Messages: {stats.get('messages', 0)}")
                status.append(f"- Media files: {stats.get('media', 0)}")
                status.append(f"- Last sync: {stats.get('last_sync', 'Never')}")
            
            return "\n".join(status)
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}", exc_info=True)
            return "❌ Failed to get status. Please try again later." 