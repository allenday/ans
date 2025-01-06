"""Base transport implementation."""
import logging
from abc import ABC, abstractmethod
from typing import Optional

from chronicler.frames.base import Frame

logger = logging.getLogger(__name__)

class BaseTransport(ABC):
    """Base class for transport implementations."""
    
    def __init__(self):
        """Initialize base transport."""
        logger.debug("TRANSPORT - Initialized BaseTransport")
    
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