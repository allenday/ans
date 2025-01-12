"""Media frame classes for the pipeline."""
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

from .base import Frame

logger = logging.getLogger(__name__)

@dataclass
class MediaFrame(Frame):
    """Base class for all media frames."""
    content: bytes

    def __post_init__(self):
        """Log media frame initialization."""
        if not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        logger.debug(f"FRAME - Initializing MediaFrame with {len(self.content)} bytes")
        super().__post_init__()

@dataclass
class TextFrame(Frame):
    """A frame containing text data."""
    content: str
    
    def __post_init__(self):
        """Log text frame initialization."""
        if not isinstance(self.content, str):
            raise TypeError("content must be a string")
        logger.debug(f"FRAME - Initializing TextFrame with {len(self.content)} chars")
        super().__post_init__()

@dataclass
class ImageFrame(MediaFrame):
    """A frame containing image data."""
    size: Tuple[int, int]
    format: str
    
    def __post_init__(self):
        """Log image frame initialization."""
        if not isinstance(self.size, tuple) or len(self.size) != 2 or not all(isinstance(x, int) for x in self.size):
            raise TypeError("size must be a tuple of two integers")
        if not isinstance(self.format, str):
            raise TypeError("format must be a string")
        logger.debug(f"FRAME - Initializing ImageFrame: size={self.size}, format={self.format}")
        super().__post_init__()

@dataclass
class DocumentFrame(MediaFrame):
    """A frame containing a document."""
    filename: str
    mime_type: str
    caption: Optional[str] = None
    
    def __post_init__(self):
        """Log document frame initialization."""
        if not isinstance(self.filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(self.mime_type, str):
            raise TypeError("mime_type must be a string")
        if self.caption is not None and not isinstance(self.caption, str):
            raise TypeError("caption must be a string or None")
        logger.debug(f"FRAME - Initializing DocumentFrame: filename={self.filename}, type={self.mime_type}")
        if self.caption:
            self.text = self.caption
        super().__post_init__()

@dataclass
class AudioFrame(MediaFrame):
    """A frame containing audio data."""
    duration: int  # Duration in seconds
    mime_type: str
    
    def __post_init__(self):
        """Log audio frame initialization."""
        if not isinstance(self.duration, int):
            raise TypeError("duration must be an integer")
        if not isinstance(self.mime_type, str):
            raise TypeError("mime_type must be a string")
        logger.debug(f"FRAME - Initializing AudioFrame: duration={self.duration}s, type={self.mime_type}")
        super().__post_init__()

@dataclass
class VoiceFrame(MediaFrame):
    """A frame containing voice message data."""
    duration: int  # Duration in seconds
    mime_type: str
    
    def __post_init__(self):
        """Log voice frame initialization."""
        if not isinstance(self.duration, int):
            raise TypeError("duration must be an integer")
        if not isinstance(self.mime_type, str):
            raise TypeError("mime_type must be a string")
        logger.debug(f"FRAME - Initializing VoiceFrame: duration={self.duration}s, type={self.mime_type}")
        super().__post_init__()

@dataclass
class StickerFrame(MediaFrame):
    """A frame containing sticker data."""
    emoji: str
    set_name: str
    
    def __post_init__(self):
        """Log sticker frame initialization."""
        if not isinstance(self.emoji, str):
            raise TypeError("emoji must be a string")
        if not isinstance(self.set_name, str):
            raise TypeError("set_name must be a string")
        logger.debug(f"FRAME - Initializing StickerFrame: emoji={self.emoji}, set={self.set_name}")
        super().__post_init__() 