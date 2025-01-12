"""Command processor implementation."""
from chronicler.logging import get_logger, trace_operation
from typing import Dict, Type, Optional

from chronicler.frames.base import Frame
from chronicler.processors.base import BaseProcessor
from chronicler.frames.media import TextFrame
from chronicler.frames.command import CommandFrame
from .handlers import CommandHandler

logger = get_logger(__name__)

class CommandProcessor(BaseProcessor):
    """Processes command frames by routing them to appropriate handlers."""
    
    def __init__(self):
        """Initialize the command processor."""
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.info("COMMAND - Initializing command processor")
        self._handlers: Dict[str, CommandHandler] = {}
        self.logger.debug("COMMAND - No handlers registered")
        
    @trace_operation('commands.processor')
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame, routing commands to appropriate handlers."""
        if not isinstance(frame, CommandFrame):
            self.logger.debug(f"COMMAND - Ignoring non-command frame: {type(frame)}")
            return None
            
        return await self.process_frame(frame)
        
    @trace_operation('commands.processor')
    async def process_frame(self, frame: CommandFrame) -> Frame:
        """Process a command frame."""
        command = frame.command
        args = frame.args
        metadata = frame.metadata

        self.logger.info(f"COMMAND - Processing command: {command} from user {metadata.get('sender_id', 'unknown')}")
        self.logger.debug(f"COMMAND - Command args: {args}")
        self.logger.debug(f"COMMAND - Command metadata: {metadata}")

        if command not in self._handlers:
            self.logger.error(f"COMMAND - No handler registered for command: {command}")
            return TextFrame(text=f"Unknown command: {command}", metadata=metadata)

        handler = self._handlers[command]
        self.logger.debug(f"COMMAND - Using handler {handler.__class__.__name__} for {command}")

        # Let exceptions propagate
        result = await handler.handle(frame)
        return result
            
    @trace_operation('commands.processor')
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