"""Media frame classes for the pipeline."""
from chronicler.logging import get_logger
from dataclasses import dataclass, KW_ONLY
from typing import Optional, Tuple

from .base import Frame

logger = get_logger(__name__)

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
class ImageFrame(Frame):
    """Frame containing image data."""

    content: bytes
    size: Optional[Tuple[int, int]] = None
    format: Optional[str] = None
    caption: Optional[str] = None

    def __post_init__(self):
        """Validate the frame data."""
        if not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        if self.size is not None and (not isinstance(self.size, tuple) or len(self.size) != 2 or not all(isinstance(x, int) for x in self.size)):
            raise TypeError("size must be a tuple of two integers")
        if self.format is not None and not isinstance(self.format, str):
            raise TypeError("format must be a string")
        if self.caption is not None and not isinstance(self.caption, str):
            raise TypeError("caption must be a string")
        logger.debug(f"FRAME - Initializing ImageFrame: size={self.size}, format={self.format}")
        if self.caption:
            self.text = self.caption
        super().__post_init__()

@dataclass
class DocumentFrame(Frame):
    """A frame containing a document."""
    _: KW_ONLY
    filename: str
    mime_type: str
    content: Optional[bytes] = None
    caption: Optional[str] = None
    
    def __post_init__(self):
        """Log document frame initialization."""
        if not isinstance(self.filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(self.mime_type, str):
            raise TypeError("mime_type must be a string")
        if self.content is not None and not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        if self.caption is not None and not isinstance(self.caption, str):
            raise TypeError("caption must be a string")
        logger.debug(f"FRAME - Initializing DocumentFrame: {self.filename} ({self.mime_type})")
        if self.caption:
            self.text = self.caption
        super().__post_init__()

@dataclass
class AudioFrame(Frame):
    """A frame containing audio data."""
    _: KW_ONLY
    duration: int  # Duration in seconds
    mime_type: str
    content: Optional[bytes] = None
    
    def __post_init__(self):
        """Log audio frame initialization."""
        if not isinstance(self.duration, int):
            raise TypeError("duration must be an integer")
        if not isinstance(self.mime_type, str):
            raise TypeError("mime_type must be a string")
        if self.content is not None and not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        logger.debug(f"FRAME - Initializing AudioFrame: duration={self.duration}s, type={self.mime_type}")
        super().__post_init__()

@dataclass
class VoiceFrame(Frame):
    """A frame containing voice message data."""
    _: KW_ONLY
    duration: int  # Duration in seconds
    mime_type: str
    content: Optional[bytes] = None
    
    def __post_init__(self):
        """Log voice frame initialization."""
        if not isinstance(self.duration, int):
            raise TypeError("duration must be an integer")
        if not isinstance(self.mime_type, str):
            raise TypeError("mime_type must be a string")
        if self.content is not None and not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        logger.debug(f"FRAME - Initializing VoiceFrame: duration={self.duration}s, type={self.mime_type}")
        super().__post_init__()

@dataclass
class StickerFrame(Frame):
    """A frame containing sticker data."""
    content: bytes
    emoji: Optional[str] = None
    set_name: Optional[str] = None
    format: Optional[str] = None
    
    def __post_init__(self):
        """Log sticker frame initialization."""
        if not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        if self.emoji is not None and not isinstance(self.emoji, str):
            raise TypeError("emoji must be a string")
        if self.set_name is not None and not isinstance(self.set_name, str):
            raise TypeError("set_name must be a string")
        if self.format is not None and not isinstance(self.format, str):
            raise TypeError("format must be a string")
        logger.debug(f"FRAME - Initializing StickerFrame: emoji={self.emoji}, set_name={self.set_name}, format={self.format}")
        super().__post_init__() 