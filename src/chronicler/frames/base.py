"""Base frame class for the pipeline."""
import logging
from dataclasses import dataclass, field, KW_ONLY
from typing import Optional, Dict, Any
from abc import ABC

logger = logging.getLogger(__name__)

@dataclass
class Frame(ABC):
    """Base frame class."""
    _: KW_ONLY
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Log frame creation."""
        logger.debug(f"FRAME - Created {self.__class__.__name__} with metadata: {self.metadata}") 