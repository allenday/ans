"""Pipeline implementation."""
from chronicler.logging import get_logger
from typing import List, Optional
from chronicler.frames.base import Frame
from chronicler.processors.base import BaseProcessor

logger = get_logger(__name__)

class Pipeline:
    """A pipeline that processes frames through a series of processors."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.processors: List[BaseProcessor] = []
        logger.info("PIPELINE - Initialized empty pipeline")
        
    def add_processor(self, processor: BaseProcessor) -> None:
        """Add a processor to the pipeline."""
        if not isinstance(processor, BaseProcessor):
            logger.error(f"PIPELINE - Invalid processor type: {type(processor)} (must be BaseProcessor)")
            raise TypeError("Processor must be an instance of BaseProcessor")
        self.processors.append(processor)
        logger.info(f"PIPELINE - Added processor: {processor.__class__.__name__} (total: {len(self.processors)})")
        
    async def process(self, frame: Frame) -> Optional[Frame]:
        """Process a frame through all processors in sequence."""
        logger.info(f"PIPELINE - Processing frame of type {type(frame).__name__}")
        current_frame = frame
        
        for i, processor in enumerate(self.processors, 1):
            try:
                logger.debug(f"PIPELINE - Running processor {i}/{len(self.processors)}: {processor.__class__.__name__}")
                result = await processor.process(current_frame)
                if result is not None:
                    logger.debug(f"PIPELINE - Processor {processor.__class__.__name__} transformed frame to {type(result).__name__}")
                    current_frame = result
                else:
                    logger.debug(f"PIPELINE - Processor {processor.__class__.__name__} returned None, keeping current frame")
            except Exception as e:
                logger.error(
                    f"PIPELINE - Error in processor {processor.__class__.__name__} ({i}/{len(self.processors)}): {e}",
                    exc_info=True
                )
                raise
                
        logger.info(f"PIPELINE - Frame processing complete, final type: {type(current_frame).__name__}")
        return current_frame 