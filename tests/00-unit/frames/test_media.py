"""Tests for media frame classes."""
import pytest
from chronicler.frames.media import (
    TextFrame, ImageFrame, DocumentFrame, 
    AudioFrame, VoiceFrame, StickerFrame
)

def test_text_frame_valid():
    """Test valid TextFrame initialization."""
    frame = TextFrame(content="test message")
    assert frame.content == "test message"
    assert frame.metadata == {"type": "textframe"}

def test_text_frame_invalid_content():
    """Test TextFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be a string"):
        TextFrame(content=123)

def test_text_frame_with_metadata():
    """Test TextFrame with metadata."""
    metadata = {"chat_id": 123, "message_id": 456}
    frame = TextFrame(content="test", metadata=metadata)
    assert frame.metadata == metadata

def test_image_frame_valid():
    """Test valid ImageFrame initialization."""
    frame = ImageFrame(
        content=b"test_image",
        size=(100, 200),
        format="jpeg",
        caption="test caption"
    )
    assert frame.content == b"test_image"
    assert frame.size == (100, 200)
    assert frame.format == "jpeg"
    assert frame.caption == "test caption"
    assert frame.text == "test caption"  # Caption should be copied to text

def test_image_frame_minimal():
    """Test ImageFrame with only required fields."""
    frame = ImageFrame(content=b"test_image")
    assert frame.content == b"test_image"
    assert frame.size is None
    assert frame.format is None
    assert frame.caption is None

def test_image_frame_invalid_content():
    """Test ImageFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        ImageFrame(content="not bytes")

def test_image_frame_invalid_size():
    """Test ImageFrame with invalid size."""
    with pytest.raises(TypeError, match="size must be a tuple of two integers"):
        ImageFrame(content=b"test", size=(1, 2, 3))
    with pytest.raises(TypeError, match="size must be a tuple of two integers"):
        ImageFrame(content=b"test", size="100x200")
    with pytest.raises(TypeError, match="size must be a tuple of two integers"):
        ImageFrame(content=b"test", size=(1.5, 2.5))

def test_image_frame_invalid_format():
    """Test ImageFrame with invalid format."""
    with pytest.raises(TypeError, match="format must be a string"):
        ImageFrame(content=b"test", format=123)

def test_image_frame_invalid_caption():
    """Test ImageFrame with invalid caption."""
    with pytest.raises(TypeError, match="caption must be a string"):
        ImageFrame(content=b"test", caption=123)

def test_document_frame_valid():
    """Test valid DocumentFrame initialization."""
    frame = DocumentFrame(
        content=b"test_doc",
        filename="test.txt",
        mime_type="text/plain",
        caption="test caption"
    )
    assert frame.content == b"test_doc"
    assert frame.filename == "test.txt"
    assert frame.mime_type == "text/plain"
    assert frame.caption == "test caption"
    assert frame.text == "test caption"  # Caption should be copied to text

def test_document_frame_minimal():
    """Test DocumentFrame with only required fields."""
    frame = DocumentFrame(
        content=b"test_doc",
        filename="test.txt",
        mime_type="text/plain"
    )
    assert frame.content == b"test_doc"
    assert frame.filename == "test.txt"
    assert frame.mime_type == "text/plain"
    assert frame.caption is None

def test_document_frame_invalid_content():
    """Test DocumentFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        DocumentFrame(content="not bytes", filename="test.txt", mime_type="text/plain")

def test_document_frame_invalid_filename():
    """Test DocumentFrame with invalid filename."""
    with pytest.raises(TypeError, match="filename must be a string"):
        DocumentFrame(content=b"test", filename=123, mime_type="text/plain")

def test_document_frame_invalid_mime_type():
    """Test DocumentFrame with invalid mime_type."""
    with pytest.raises(TypeError, match="mime_type must be a string"):
        DocumentFrame(content=b"test", filename="test.txt", mime_type=123)

def test_document_frame_invalid_caption():
    """Test DocumentFrame with invalid caption."""
    with pytest.raises(TypeError, match="caption must be a string"):
        DocumentFrame(
            content=b"test",
            filename="test.txt",
            mime_type="text/plain",
            caption=123
        )

def test_audio_frame_valid():
    """Test valid AudioFrame initialization."""
    frame = AudioFrame(
        content=b"test_audio",
        duration=120,
        mime_type="audio/mp3"
    )
    assert frame.content == b"test_audio"
    assert frame.duration == 120
    assert frame.mime_type == "audio/mp3"

def test_audio_frame_invalid_content():
    """Test AudioFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        AudioFrame(content="not bytes", duration=120, mime_type="audio/mp3")

def test_audio_frame_invalid_duration():
    """Test AudioFrame with invalid duration."""
    with pytest.raises(TypeError, match="duration must be an integer"):
        AudioFrame(content=b"test", duration="120", mime_type="audio/mp3")
    with pytest.raises(TypeError, match="duration must be an integer"):
        AudioFrame(content=b"test", duration=120.5, mime_type="audio/mp3")

def test_audio_frame_invalid_mime_type():
    """Test AudioFrame with invalid mime_type."""
    with pytest.raises(TypeError, match="mime_type must be a string"):
        AudioFrame(content=b"test", duration=120, mime_type=123)

def test_voice_frame_valid():
    """Test valid VoiceFrame initialization."""
    frame = VoiceFrame(
        content=b"test_voice",
        duration=30,
        mime_type="audio/ogg"
    )
    assert frame.content == b"test_voice"
    assert frame.duration == 30
    assert frame.mime_type == "audio/ogg"

def test_voice_frame_invalid_content():
    """Test VoiceFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        VoiceFrame(content="not bytes", duration=30, mime_type="audio/ogg")

def test_voice_frame_invalid_duration():
    """Test VoiceFrame with invalid duration."""
    with pytest.raises(TypeError, match="duration must be an integer"):
        VoiceFrame(content=b"test", duration="30", mime_type="audio/ogg")
    with pytest.raises(TypeError, match="duration must be an integer"):
        VoiceFrame(content=b"test", duration=30.5, mime_type="audio/ogg")

def test_voice_frame_invalid_mime_type():
    """Test VoiceFrame with invalid mime_type."""
    with pytest.raises(TypeError, match="mime_type must be a string"):
        VoiceFrame(content=b"test", duration=30, mime_type=123)

def test_sticker_frame_valid():
    """Test valid StickerFrame initialization."""
    frame = StickerFrame(
        content=b"test_sticker",
        emoji="😀",
        set_name="test_set",
        format="webp"
    )
    assert frame.content == b"test_sticker"
    assert frame.emoji == "😀"
    assert frame.set_name == "test_set"
    assert frame.format == "webp"

def test_sticker_frame_minimal():
    """Test StickerFrame with only required fields."""
    frame = StickerFrame(content=b"test_sticker")
    assert frame.content == b"test_sticker"
    assert frame.emoji is None
    assert frame.set_name is None
    assert frame.format is None

def test_sticker_frame_invalid_content():
    """Test StickerFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        StickerFrame(content="not bytes")

def test_sticker_frame_invalid_emoji():
    """Test StickerFrame with invalid emoji."""
    with pytest.raises(TypeError, match="emoji must be a string"):
        StickerFrame(content=b"test", emoji=123)

def test_sticker_frame_invalid_set_name():
    """Test StickerFrame with invalid set_name."""
    with pytest.raises(TypeError, match="set_name must be a string"):
        StickerFrame(content=b"test", set_name=123)

def test_sticker_frame_invalid_format():
    """Test StickerFrame with invalid format."""
    with pytest.raises(TypeError, match="format must be a string"):
        StickerFrame(content=b"test", format=123) 