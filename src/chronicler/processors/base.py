"""Base processor implementation."""
from abc import ABC, abstractmethod
from typing import Optional
from chronicler.logging import get_logger

from chronicler.frames.base import Frame

logger = get_logger(__name__)

class BaseProcessor(ABC):
    """Base class for frame processors."""
    
    def __init__(self):
        """Initialize base processor."""
        logger.debug("PROC - Initialized BaseProcessor")
    
    @abstractmethod
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame."""
        pass 