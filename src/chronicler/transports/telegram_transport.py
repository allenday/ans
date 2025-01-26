"""Telegram transport base class."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from telethon import TelegramClient
from telegram.ext import Application
import time

from chronicler.frames.base import Frame
from chronicler.transports.base import BaseTransport
from chronicler.logging import get_logger, trace_operation

logger = get_logger("chronicler.transports.telegram")

class TelegramTransportBase(BaseTransport, ABC):
    """Base class for Telegram transports."""
    
    def __init__(self):
        super().__init__()
        self._start_time = None
        self._message_count = 0
        self._command_count = 0
        self._error_count = 0
        self._command_handlers = {}
        self.on_command = self.register_command  # Alias for command registration
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def start(self):
        """Start the transport."""
        self._start_time = time.time()
        logger.info("Starting transport")
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def stop(self):
        """Stop the transport."""
        uptime = time.time() - (self._start_time or time.time())
        logger.info(f"Stopping transport. Stats: uptime={uptime:.2f}s, messages={self._message_count}, commands={self._command_count}, errors={self._error_count}")
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def process_frame(self, frame: Frame):
        """Process a frame."""
        pass
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def send(self, frame: Frame) -> Optional[Frame]:
        """Send a frame."""
        pass
    
    @abstractmethod
    @trace_operation('transport.telegram.base')
    async def register_command(self, command: str, handler: callable):
        """Register a command handler.
        
        Args:
            command: Command string without leading slash (e.g. "start" for /start)
            handler: Async callback function that takes (frame: CommandFrame) as argument
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transport statistics."""
        uptime = time.time() - (self._start_time or time.time())
        return {
            'uptime': f"{uptime:.2f}s",
            'messages': self._message_count,
            'commands': self._command_count,
            'errors': self._error_count
        }
