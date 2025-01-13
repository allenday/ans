"""Unit tests for frame classes."""
import pytest

from chronicler.frames.base import Frame
from chronicler.frames.media import (
    TextFrame,
    ImageFrame,
    DocumentFrame,
    AudioFrame,
    VoiceFrame,
    StickerFrame,
)

def test_text_frame_creation():
    """Test text frame creation."""
    frame = TextFrame(content="test message", metadata={})
    assert isinstance(frame, Frame)
    assert frame.content == "test message"

def test_text_frame_validation():
    """Test text frame validation."""
    with pytest.raises(TypeError):
        TextFrame(content=123, metadata={})

def test_image_frame_creation():
    """Test image frame creation."""
    frame = ImageFrame(
        content=b"test_data",
        size=(100, 100),
        format="jpeg",
        metadata={}
    )
    assert isinstance(frame, Frame)
    assert frame.content == b"test_data"
    assert frame.size == (100, 100)
    assert frame.format == "jpeg"

def test_image_frame_validation():
    """Test image frame validation."""
    with pytest.raises(TypeError):
        ImageFrame(
            content="not_bytes",
            size=(100, 100),
            format="jpeg",
            metadata={}
        )

def test_document_frame_creation():
    """Test document frame creation."""
    frame = DocumentFrame(
        content=b"test_data",
        filename="test.txt",
        mime_type="text/plain",
        caption="Test document",
        metadata={}
    )
    assert isinstance(frame, Frame)
    assert frame.content == b"test_data"
    assert frame.filename == "test.txt"
    assert frame.mime_type == "text/plain"
    assert frame.caption == "Test document"
    assert frame.text == "Test document"

def test_document_frame_validation():
    """Test document frame validation."""
    with pytest.raises(TypeError):
        DocumentFrame(
            content="not_bytes",
            filename=123,
            mime_type="text/plain",
            metadata={}
        )

def test_audio_frame_creation():
    """Test audio frame creation."""
    frame = AudioFrame(
        content=b"test_data",
        duration=60,
        mime_type="audio/mp3",
        metadata={}
    )
    assert isinstance(frame, Frame)
    assert frame.content == b"test_data"
    assert frame.duration == 60
    assert frame.mime_type == "audio/mp3"

def test_audio_frame_validation():
    """Test audio frame validation."""
    with pytest.raises(TypeError):
        AudioFrame(
            content="not_bytes",
            duration="not_int",
            mime_type="audio/mp3",
            metadata={}
        )

def test_voice_frame_creation():
    """Test voice frame creation."""
    frame = VoiceFrame(
        content=b"test_data",
        duration=30,
        mime_type="audio/ogg",
        metadata={}
    )
    assert isinstance(frame, Frame)
    assert frame.content == b"test_data"
    assert frame.duration == 30
    assert frame.mime_type == "audio/ogg"

def test_voice_frame_validation():
    """Test voice frame validation."""
    with pytest.raises(TypeError):
        VoiceFrame(
            content="not_bytes",
            duration="not_int",
            mime_type="audio/ogg",
            metadata={}
        )

def test_sticker_frame_creation():
    """Test sticker frame creation."""
    frame = StickerFrame(
        content=b"test_data",
        emoji="👍",
        set_name="test_set",
        metadata={}
    )
    assert isinstance(frame, Frame)
    assert frame.content == b"test_data"
    assert frame.emoji == "👍"
    assert frame.set_name == "test_set"

def test_sticker_frame_validation():
    """Test sticker frame validation."""
    with pytest.raises(TypeError):
        StickerFrame(
            content="not_bytes",
            emoji=123,
            set_name=456,
            metadata={}
        )

def test_frame_metadata():
    """Test frame metadata handling."""
    metadata = {"user_id": 123, "chat_id": 456}
    frame = TextFrame(content="test", metadata=metadata)
    assert frame.metadata == metadata

def test_frame_inheritance():
    """Test frame inheritance hierarchy."""
    frames = [
        TextFrame(content="test", metadata={}),
        ImageFrame(content=b"test", size=(100, 100), format="jpeg", metadata={}),
        DocumentFrame(content=b"test", filename="test.txt", mime_type="text/plain", metadata={}),
        AudioFrame(content=b"test", duration=60, mime_type="audio/mp3", metadata={}),
        VoiceFrame(content=b"test", duration=30, mime_type="audio/ogg", metadata={}),
        StickerFrame(content=b"test", emoji="👍", set_name="test_set", metadata={})
    ]
    
    for frame in frames:
        assert isinstance(frame, Frame) 