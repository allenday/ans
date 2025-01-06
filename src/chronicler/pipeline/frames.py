from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any
from abc import ABC

class Frame(ABC):
    """Base frame class."""
    pass

@dataclass
class TextFrame(Frame):
    """A frame containing text data."""
    text: str
    metadata: Optional[Dict[str, Any]] = field(default=None)

@dataclass
class ImageFrame(Frame):
    """A frame containing image data."""
    image: bytes
    size: Tuple[int, int]
    format: str
    metadata: Optional[Dict[str, Any]] = field(default=None)

@dataclass
class DocumentFrame(Frame):
    """A frame containing a document."""
    content: bytes
    filename: str
    mime_type: str
    metadata: Optional[Dict[str, Any]] = field(default=None)
    caption: Optional[str] = field(default=None) 