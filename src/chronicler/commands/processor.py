"""Command processor implementation."""
import logging
from typing import Dict, Type
from chronicler.pipeline import Frame, BaseProcessor
from .frames import CommandFrame
from .handlers import CommandHandler

logger = logging.getLogger(__name__)

class CommandProcessor(BaseProcessor):
    """Processes command frames by routing them to appropriate handlers."""
    
    def __init__(self):
        """Initialize the command processor."""
        super().__init__()
        logger.info("CMD - Initializing command processor")
        self._handlers: Dict[str, CommandHandler] = {}
        
    async def process_frame(self, frame: Frame) -> None:
        """Process a frame, routing commands to appropriate handlers."""
        if not isinstance(frame, CommandFrame):
            logger.debug(f"CMD - Ignoring non-command frame: {type(frame)}")
            return
            
        logger.info(f"CMD - Processing command: {frame.command}")
        logger.debug(f"CMD - Command args: {frame.args}")
        logger.debug(f"CMD - Command metadata: {frame.metadata}")
        
        try:
            if handler := self._handlers.get(frame.command.lower()):
                logger.debug(f"CMD - Using handler {handler.__class__.__name__}")
                await handler.handle(frame)
            else:
                logger.warning(f"CMD - Unknown command: {frame.command}")
                response = "Unknown command. Available commands: /start, /config, /status"
                await self.push_frame(Frame(text=response))
            
            logger.debug("CMD - Command processing complete")
            
        except Exception as e:
            logger.error(f"CMD - Error processing command {frame.command}: {e}", exc_info=True)
            await self.push_frame(Frame(text=f"Error processing command: {str(e)}"))
            
    def register_handler(self, command: str, handler: Type[CommandHandler]) -> None:
        """Register a handler for a command."""
        if not command.startswith('/'):
            raise ValueError("Command must start with '/'")
            
        if handler is None:
            raise ValueError("Handler cannot be None")
            
        command = command.lower()
        logger.debug(f"CMD - Registering handler for command {command}: {handler.__class__.__name__}")
        self._handlers[command] = handler 