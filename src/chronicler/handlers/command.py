"""Command handler implementations."""
import logging
from typing import Optional

from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.storage import StorageAdapter
from chronicler.storage.interface import User, Topic

logger = logging.getLogger(__name__)

class CommandHandler:
    """Base class for command handlers."""
    
    def __init__(self, coordinator: StorageAdapter):
        """Initialize command handler."""
        self.coordinator = coordinator
    
    def handle(self, frame: CommandFrame) -> Optional[Frame]:
        """Handle a command frame."""
        raise NotImplementedError("Command handlers must implement handle()")

class StartCommandHandler(CommandHandler):
    """Handler for /start command."""
    
    async def handle(self, frame: CommandFrame) -> Optional[Frame]:
        """Handle /start command."""
        try:
            logger.debug("HANDLER - Processing /start command")
            user = User(
                id=str(frame.metadata.get("chat_id")),
                name=frame.metadata.get("username", "unknown"),
                metadata=frame.metadata
            )
            await self.coordinator.init_storage(user)
            topic = Topic(
                id="default",
                name="Default Topic",
                metadata={"chat_id": frame.metadata.get("chat_id")}
            )
            await self.coordinator.create_topic(topic)
            return TextFrame(
                text="Welcome to Chronicler! I'll help you archive your chat messages.",
                metadata=frame.metadata
            )
        except Exception as e:
            logger.error(f"HANDLER - Error handling /start command: {e}")
            raise

class ConfigCommandHandler(CommandHandler):
    """Handler for /config command."""
    
    async def handle(self, frame: CommandFrame) -> Optional[Frame]:
        """Handle /config command."""
        try:
            logger.debug("HANDLER - Processing /config command")
            if len(frame.args) != 3:
                return TextFrame(
                    text="Usage: /config <repository> <branch> <token>\nExample: /config owner/repo main ghp_token123",
                    metadata=frame.metadata
                )
            
            await self.coordinator.set_github_config(
                token=frame.args[2],  # token
                repo=frame.args[0]    # repository
            )
            return TextFrame(
                text="GitHub configuration updated successfully.",
                metadata=frame.metadata
            )
        except Exception as e:
            logger.error(f"HANDLER - Error handling /config command: {e}")
            raise

class StatusCommandHandler(CommandHandler):
    """Handler for /status command."""
    
    async def handle(self, frame: CommandFrame) -> Optional[Frame]:
        """Handle /status command."""
        try:
            logger.debug("HANDLER - Processing /status command")
            await self.coordinator.sync()
            return TextFrame(
                text="Chronicler Status:\n- Storage: Initialized\n- GitHub: Connected\n- Last sync: Success",
                metadata=frame.metadata
            )
        except Exception as e:
            logger.error(f"HANDLER - Error handling /status command: {e}")
            raise 