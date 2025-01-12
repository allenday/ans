"""Base frame class for the pipeline."""
from chronicler.logging import get_logger
from dataclasses import dataclass, field, KW_ONLY
from typing import Optional, Dict, Any
from abc import ABC

logger = get_logger("chronicler.frames.base")

@dataclass
class Frame(ABC):
    """Base frame class."""
    _: KW_ONLY
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Log frame creation."""
        logger.debug(f"FRAME - Created {self.__class__.__name__} with metadata: {self.metadata}") 