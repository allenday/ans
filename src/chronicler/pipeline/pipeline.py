"""Pipeline infrastructure."""
import logging
from typing import List
from .frames import Frame
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class Pipeline:
    """A pipeline that processes frames through a series of processors."""
    
    def __init__(self, processors: List['BaseProcessor'] = None):
        """Initialize the pipeline with optional processors."""
        logger.info("PIPE - Initializing pipeline")
        self.processors = processors or []
        logger.debug(f"PIPE - Added {len(self.processors)} processors")
        
        # Link processors
        for i in range(len(self.processors) - 1):
            logger.debug(f"PIPE - Linking {self.processors[i].__class__.__name__} to {self.processors[i + 1].__class__.__name__}")
            self.processors[i].next_processor = self.processors[i + 1]
        
    async def process_frame(self, frame: Frame) -> None:
        """Process a frame through all processors in sequence."""
        logger.info(f"PIPE - Processing frame of type {type(frame).__name__}")
        try:
            if self.processors:
                logger.debug(f"PIPE - Starting pipeline with {len(self.processors)} processors")
                await self.processors[0].process_frame(frame)
                logger.debug("PIPE - Frame processing complete")
            else:
                logger.warning("PIPE - Attempted to process frame through empty pipeline")
        except Exception as e:
            logger.error(f"PIPE - Failed to process frame: {e}", exc_info=True)
            raise

class BaseProcessor:
    """Base class for frame processors."""
    
    def __init__(self):
        """Initialize the processor."""
        self.next_processor = None
    
    async def process_frame(self, frame: Frame) -> None:
        """Process a frame. Must be implemented by subclasses."""
        raise NotImplementedError("Processors must implement process_frame")
        
    async def push_frame(self, frame: Frame) -> None:
        """Push a frame to the next processor in the pipeline."""
        if self.next_processor:
            await self.next_processor.process_frame(frame)

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