"""Command processor implementation."""
from chronicler.logging import get_logger, trace_operation
from typing import Dict, Type, Optional

from chronicler.frames.base import Frame
from chronicler.processors.base import BaseProcessor
from chronicler.frames.media import TextFrame
from chronicler.frames.command import CommandFrame
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.handlers.command import CommandHandler, StartCommandHandler, ConfigCommandHandler, StatusCommandHandler

logger = get_logger(__name__)

class CommandProcessor(BaseProcessor):
    """Processor for handling command frames."""
    
    def __init__(self, storage: StorageCoordinator):
        """Initialize command processor."""
        super().__init__()
        self.storage = storage
        self.handlers: Dict[str, CommandHandler] = {}
        
        # Register default handlers
        self.register_handler("/start", StartCommandHandler(storage))
        self.register_handler("/config", ConfigCommandHandler(storage))
        self.register_handler("/status", StatusCommandHandler(storage))
        
        logger.debug("PROC - Initialized CommandProcessor")
    
    def register_handler(self, command: str, handler: CommandHandler) -> None:
        """Register a command handler."""
        self.handlers[command] = handler
        logger.debug(f"PROC - Registered handler for {command}")
    
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a command frame."""
        try:
            if not isinstance(frame, CommandFrame):
                logger.debug("PROC - Not a command frame, skipping")
                return None
            
            handler = self.handlers.get(frame.command)
            if not handler:
                logger.warning(f"PROC - No handler for command: {frame.command}")
                return TextFrame(
                    content=f"Unknown command: {frame.command}",
                    metadata=frame.metadata
                )
            
            logger.debug(f"PROC - Processing command: {frame.command}")
            return await handler.handle(frame)
            
        except Exception as e:
            logger.error(f"PROC - Error processing command: {e}")
            raise 