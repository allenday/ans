"""Frame classes for the pipeline."""
import logging
from dataclasses import dataclass, field, KW_ONLY
from typing import Optional, Tuple, Dict, Any
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

@dataclass
class TextFrame(Frame):
    """A frame containing text data."""
    text: str
    
    def __post_init__(self):
        """Log text frame initialization."""
        logger.debug(f"FRAME - Initializing TextFrame with {len(self.text)} chars")
        super().__post_init__()

@dataclass
class ImageFrame(Frame):
    """A frame containing image data."""
    image: bytes
    size: Tuple[int, int]
    format: str
    
    def __post_init__(self):
        """Log image frame initialization."""
        logger.debug(f"FRAME - Initializing ImageFrame: size={self.size}, format={self.format}")
        super().__post_init__()

@dataclass
class DocumentFrame(Frame):
    """A frame containing a document."""
    content: bytes
    filename: str
    mime_type: str
    caption: Optional[str] = None
    
    def __post_init__(self):
        """Log document frame initialization."""
        logger.debug(f"FRAME - Initializing DocumentFrame: filename={self.filename}, type={self.mime_type}")
        if self.caption:
            self.text = self.caption
        super().__post_init__()

@dataclass
class AudioFrame(Frame):
    """A frame containing audio data."""
    audio: bytes
    duration: int  # Duration in seconds
    mime_type: str
    
    def __post_init__(self):
        """Log audio frame initialization."""
        logger.debug(f"FRAME - Initializing AudioFrame: duration={self.duration}s, type={self.mime_type}")
        super().__post_init__()

@dataclass
class VoiceFrame(Frame):
    """A frame containing voice message data."""
    audio: bytes
    duration: int  # Duration in seconds
    mime_type: str
    
    def __post_init__(self):
        """Log voice frame initialization."""
        logger.debug(f"FRAME - Initializing VoiceFrame: duration={self.duration}s, type={self.mime_type}")
        super().__post_init__()

@dataclass
class StickerFrame(Frame):
    """A frame containing sticker data."""
    sticker: bytes
    emoji: str
    set_name: str
    
    def __post_init__(self):
        """Log sticker frame initialization."""
        logger.debug(f"FRAME - Initializing StickerFrame: emoji={self.emoji}, set={self.set_name}")
        super().__post_init__() 