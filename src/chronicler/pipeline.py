from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from chronicler.frames import Frame

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """Base class for all processors in the pipeline."""
    
    def __init__(self):
        self.next_processor: Optional[BaseProcessor] = None
        logger.debug(f"Initialized {self.__class__.__name__}")
        
    async def push_frame(self, frame: Frame):
        """Push a frame to the next processor in the pipeline."""
        if self.next_processor:
            logger.debug(f"Pushing {type(frame).__name__} from {self.__class__.__name__} to {self.next_processor.__class__.__name__}")
            await self.next_processor.process_frame(frame)
        else:
            logger.debug(f"No next processor for {type(frame).__name__} in {self.__class__.__name__}")
    
    @abstractmethod
    async def process_frame(self, frame: Frame):
        """Process a frame."""
        pass

class Pipeline:
    """A pipeline that processes frames through a series of processors."""
    
    def __init__(self, processors: List[BaseProcessor]):
        self.processors = processors
        logger.info(f"Creating pipeline with {len(processors)} processors")
        # Link processors
        for i in range(len(processors) - 1):
            logger.debug(f"Linking {processors[i].__class__.__name__} to {processors[i + 1].__class__.__name__}")
            processors[i].next_processor = processors[i + 1]
    
    async def process_frame(self, frame: Frame):
        """Process a frame through the pipeline."""
        if self.processors:
            logger.debug(f"Starting pipeline processing for {type(frame).__name__}")
            await self.processors[0].process_frame(frame)
        else:
            logger.warning("Attempted to process frame through empty pipeline")

class BaseTransport(BaseProcessor):
    """Base class for transports that handle input/output."""
    
    @abstractmethod
    async def start(self):
        """Start the transport."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the transport."""
        pass 