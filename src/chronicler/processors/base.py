"""Base processor implementation."""
from abc import ABC, abstractmethod
from typing import Optional, List
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

class ProcessorChain(BaseProcessor):
    """Chain of processors that process frames in sequence."""
    
    def __init__(self, processors: Optional[List[BaseProcessor]] = None):
        """Initialize processor chain."""
        super().__init__()
        self.processors = processors or []
        logger.debug(f"PROC - Initialized ProcessorChain with {len(self.processors)} processors")
    
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process frame through chain of processors."""
        current_frame = frame
        for processor in self.processors:
            if current_frame is None:
                break
            current_frame = await processor.process(current_frame)
        return current_frame
    
    def add_processor(self, processor: BaseProcessor) -> None:
        """Add a processor to the chain."""
        self.processors.append(processor)
        logger.debug(f"PROC - Added processor {processor.__class__.__name__} to chain") 