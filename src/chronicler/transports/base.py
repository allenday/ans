"""Base transport implementation."""
from abc import ABC, abstractmethod
from typing import Optional
from chronicler.logging import get_logger
from chronicler.exceptions import TransportError
from chronicler.frames.base import Frame
from chronicler.processors.base import BaseProcessor

class BaseTransport(BaseProcessor, ABC):
    """Base class for all transports."""

    def __init__(self):
        """Initialize the transport."""
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.debug("TRANSPORT - Initialized BaseTransport")
        self._start_time = None
        self._message_count = 0
        self._error_count = 0
        self._initialized = False
    
    @abstractmethod
    async def start(self) -> None:
        """Start the transport."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport."""
        pass
    
    @abstractmethod
    async def send(self, frame: Frame) -> Optional[Frame]:
        """Send a frame through the transport."""
        pass

    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame by sending it through the transport."""
        return await self.send(frame) 