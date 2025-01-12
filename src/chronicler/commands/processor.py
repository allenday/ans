"""Command processor implementation."""
from chronicler.logging import get_logger
from typing import Dict, Type, Optional

from chronicler.frames.base import Frame
from chronicler.processors.base import BaseProcessor
from chronicler.frames.media import TextFrame
from .frames import CommandFrame
from .handlers import CommandHandler

logger = get_logger(__name__)

class CommandProcessor(BaseProcessor):
    """Processes command frames by routing them to appropriate handlers."""
    
    def __init__(self):
        """Initialize the command processor."""
        super().__init__()
        logger.info("COMMAND - Initializing command processor")
        self._handlers: Dict[str, CommandHandler] = {}
        logger.debug("COMMAND - No handlers registered")
        
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame, routing commands to appropriate handlers."""
        return await self.process_frame(frame)
        
    async def process_frame(self, frame: Frame) -> Optional[Frame]:
        """Process a frame, routing commands to appropriate handlers."""
        if not isinstance(frame, CommandFrame):
            logger.debug(f"COMMAND - Ignoring non-command frame: {type(frame)}")
            return None
            
        logger.info(f"COMMAND - Processing command: {frame.command} from user {frame.metadata.get('sender_id', 'unknown')}")
        logger.debug(f"COMMAND - Command args: {frame.args}")
        logger.debug(f"COMMAND - Command metadata: {frame.metadata}")
        
        try:
            if handler := self._handlers.get(frame.command.lower()):
                logger.debug(f"COMMAND - Using handler {handler.__class__.__name__} for {frame.command}")
                result = await handler.handle(frame)
                logger.info(f"COMMAND - Successfully handled {frame.command} command")
                return result
            else:
                logger.warning(f"COMMAND - Unknown command received: {frame.command}")
                return TextFrame(
                    text="Unknown command. Available commands: /start, /config, /status",
                    metadata=frame.metadata
                )
            
        except Exception as e:
            logger.error(
                f"COMMAND - Error processing command {frame.command} from user {frame.metadata.get('sender_id', 'unknown')}: {e}",
                exc_info=True
            )
            raise
            
    def register_handler(self, command: str, handler: CommandHandler) -> None:
        """Register a handler for a command."""
        if not command.startswith('/'):
            logger.error(f"COMMAND - Invalid command format: {command} (must start with '/')")
            raise ValueError("Command must start with '/'")
            
        if handler is None:
            logger.error("COMMAND - Attempted to register None as handler")
            raise ValueError("Handler cannot be None")
            
        if not isinstance(handler, CommandHandler):
            logger.error(f"COMMAND - Invalid handler type: {type(handler)} (must be CommandHandler)")
            raise ValueError("Handler must be an instance of CommandHandler")
            
        command = command.lower()
        logger.info(f"COMMAND - Registering handler {handler.__class__.__name__} for command {command}")
        if command in self._handlers:
            logger.warning(f"COMMAND - Overwriting existing handler for {command}")
        self._handlers[command] = handler 