"""Unit tests for media frame classes."""
import pytest
from unittest.mock import patch
from chronicler.frames import TextFrame, ImageFrame, DocumentFrame, AudioFrame, VoiceFrame, StickerFrame


# TextFrame Tests
def test_text_frame_valid():
    """Test TextFrame with valid string content."""
    content = "Test message"
    frame = TextFrame(content=content)
    assert frame.content == content


def test_text_frame_empty():
    """Test TextFrame with empty string."""
    frame = TextFrame(content="")
    assert frame.content == ""


def test_text_frame_invalid_type():
    """Test TextFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be a string"):
        TextFrame(content=123)


def test_text_frame_none():
    """Test TextFrame with None content."""
    with pytest.raises(TypeError, match="content must be a string"):
        TextFrame(content=None)


@patch('chronicler.frames.media.logger')
def test_text_frame_logging(mock_logger):
    """Test that TextFrame creation is logged."""
    content = "Test message"
    frame = TextFrame(content=content)
    
    # Verify debug log was called with correct message
    mock_logger.debug.assert_called_once()
    log_msg = mock_logger.debug.call_args[0][0]
    assert "TextFrame" in log_msg
    assert str(len(content)) in log_msg


def test_text_frame_with_metadata():
    """Test TextFrame with metadata."""
    metadata = {"source": "test", "timestamp": 123}
    frame = TextFrame(content="test", metadata=metadata)
    assert frame.metadata == metadata


def test_text_frame_with_text():
    """Test TextFrame with text field."""
    text = "Display text"
    frame = TextFrame(content="content", text=text)
    assert frame.text == text


# ImageFrame Tests
def test_image_frame_valid():
    """Test ImageFrame with valid content."""
    content = b"image data"
    size = (100, 200)
    format = "jpeg"
    caption = "Test image"
    frame = ImageFrame(content=content, size=size, format=format, caption=caption)
    assert frame.content == content
    assert frame.size == size
    assert frame.format == format
    assert frame.caption == caption


def test_image_frame_minimal():
    """Test ImageFrame with only required fields."""
    content = b"image data"
    frame = ImageFrame(content=content)
    assert frame.content == content
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
        ImageFrame(content=b"data", size=(1, 2, 3))


def test_image_frame_invalid_size_type():
    """Test ImageFrame with invalid size type."""
    with pytest.raises(TypeError, match="size must be a tuple of two integers"):
        ImageFrame(content=b"data", size="100x200")


def test_image_frame_invalid_format():
    """Test ImageFrame with invalid format type."""
    with pytest.raises(TypeError, match="format must be a string"):
        ImageFrame(content=b"data", format=123)


def test_image_frame_invalid_caption():
    """Test ImageFrame with invalid caption type."""
    with pytest.raises(TypeError, match="caption must be a string"):
        ImageFrame(content=b"data", caption=123)


@patch('chronicler.frames.media.logger')
def test_image_frame_logging(mock_logger):
    """Test that ImageFrame creation is logged."""
    frame = ImageFrame(content=b"data", size=(100, 200), format="jpeg")
    
    # Verify debug log was called with correct message
    mock_logger.debug.assert_called_once()
    log_msg = mock_logger.debug.call_args[0][0]
    assert "ImageFrame" in log_msg
    assert "(100, 200)" in log_msg
    assert "jpeg" in log_msg


def test_image_frame_with_metadata():
    """Test ImageFrame with metadata."""
    metadata = {"source": "camera", "timestamp": 123}
    frame = ImageFrame(content=b"data", metadata=metadata)
    assert frame.metadata == metadata


def test_image_frame_caption_as_text():
    """Test that caption is used as text field."""
    caption = "Test caption"
    frame = ImageFrame(content=b"data", caption=caption)
    assert frame.text == caption


# DocumentFrame Tests
def test_document_frame_valid():
    """Test DocumentFrame with valid content."""
    content = b"document data"
    filename = "test.pdf"
    mime_type = "application/pdf"
    caption = "Test document"
    frame = DocumentFrame(content=content, filename=filename, mime_type=mime_type, caption=caption)
    assert frame.content == content
    assert frame.filename == filename
    assert frame.mime_type == mime_type
    assert frame.caption == caption


def test_document_frame_minimal():
    """Test DocumentFrame with only required fields."""
    content = b"document data"
    filename = "test.txt"
    mime_type = "text/plain"
    frame = DocumentFrame(content=content, filename=filename, mime_type=mime_type)
    assert frame.content == content
    assert frame.filename == filename
    assert frame.mime_type == mime_type
    assert frame.caption is None


def test_document_frame_invalid_content():
    """Test DocumentFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        DocumentFrame(content="not bytes", filename="test.txt", mime_type="text/plain")


def test_document_frame_invalid_filename():
    """Test DocumentFrame with invalid filename type."""
    with pytest.raises(TypeError, match="filename must be a string"):
        DocumentFrame(content=b"data", filename=123, mime_type="text/plain")


def test_document_frame_invalid_mime_type():
    """Test DocumentFrame with invalid mime_type type."""
    with pytest.raises(TypeError, match="mime_type must be a string"):
        DocumentFrame(content=b"data", filename="test.txt", mime_type=123)


def test_document_frame_invalid_caption():
    """Test DocumentFrame with invalid caption type."""
    with pytest.raises(TypeError, match="caption must be a string"):
        DocumentFrame(content=b"data", filename="test.txt", mime_type="text/plain", caption=123)


@patch('chronicler.frames.media.logger')
def test_document_frame_logging(mock_logger):
    """Test that DocumentFrame creation is logged."""
    frame = DocumentFrame(content=b"data", filename="test.pdf", mime_type="application/pdf")
    
    # Verify debug log was called with correct message
    mock_logger.debug.assert_called_once()
    log_msg = mock_logger.debug.call_args[0][0]
    assert "DocumentFrame" in log_msg
    assert "test.pdf" in log_msg
    assert "application/pdf" in log_msg


def test_document_frame_with_metadata():
    """Test DocumentFrame with metadata."""
    metadata = {"source": "upload", "timestamp": 123}
    frame = DocumentFrame(content=b"data", filename="test.txt", mime_type="text/plain", metadata=metadata)
    assert frame.metadata == metadata


def test_document_frame_caption_as_text():
    """Test that caption is used as text field."""
    caption = "Test caption"
    frame = DocumentFrame(content=b"data", filename="test.txt", mime_type="text/plain", caption=caption)
    assert frame.text == caption


# AudioFrame Tests
def test_audio_frame_valid():
    """Test AudioFrame with valid content."""
    content = b"audio data"
    duration = 120
    mime_type = "audio/mp3"
    frame = AudioFrame(content=content, duration=duration, mime_type=mime_type)
    assert frame.content == content
    assert frame.duration == duration
    assert frame.mime_type == mime_type


def test_audio_frame_invalid_content():
    """Test AudioFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        AudioFrame(content="not bytes", duration=60, mime_type="audio/mp3")


def test_audio_frame_invalid_duration():
    """Test AudioFrame with invalid duration type."""
    with pytest.raises(TypeError, match="duration must be an integer"):
        AudioFrame(content=b"data", duration="60", mime_type="audio/mp3")


def test_audio_frame_invalid_mime_type():
    """Test AudioFrame with invalid mime_type type."""
    with pytest.raises(TypeError, match="mime_type must be a string"):
        AudioFrame(content=b"data", duration=60, mime_type=123)


@patch('chronicler.frames.media.logger')
def test_audio_frame_logging(mock_logger):
    """Test that AudioFrame creation is logged."""
    frame = AudioFrame(content=b"data", duration=60, mime_type="audio/mp3")
    
    # Verify debug log was called with correct message
    mock_logger.debug.assert_called_once()
    log_msg = mock_logger.debug.call_args[0][0]
    assert "AudioFrame" in log_msg
    assert "60s" in log_msg
    assert "audio/mp3" in log_msg


def test_audio_frame_with_metadata():
    """Test AudioFrame with metadata."""
    metadata = {"source": "recording", "timestamp": 123}
    frame = AudioFrame(content=b"data", duration=60, mime_type="audio/mp3", metadata=metadata)
    assert frame.metadata == metadata


# VoiceFrame Tests
def test_voice_frame_valid():
    """Test VoiceFrame with valid content."""
    content = b"voice data"
    duration = 30
    mime_type = "audio/ogg"
    frame = VoiceFrame(content=content, duration=duration, mime_type=mime_type)
    assert frame.content == content
    assert frame.duration == duration
    assert frame.mime_type == mime_type


def test_voice_frame_invalid_content():
    """Test VoiceFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        VoiceFrame(content="not bytes", duration=30, mime_type="audio/ogg")


def test_voice_frame_invalid_duration():
    """Test VoiceFrame with invalid duration type."""
    with pytest.raises(TypeError, match="duration must be an integer"):
        VoiceFrame(content=b"data", duration="30", mime_type="audio/ogg")


def test_voice_frame_invalid_mime_type():
    """Test VoiceFrame with invalid mime_type type."""
    with pytest.raises(TypeError, match="mime_type must be a string"):
        VoiceFrame(content=b"data", duration=30, mime_type=123)


@patch('chronicler.frames.media.logger')
def test_voice_frame_logging(mock_logger):
    """Test that VoiceFrame creation is logged."""
    frame = VoiceFrame(content=b"data", duration=30, mime_type="audio/ogg")
    
    # Verify debug log was called with correct message
    mock_logger.debug.assert_called_once()
    log_msg = mock_logger.debug.call_args[0][0]
    assert "VoiceFrame" in log_msg
    assert "30s" in log_msg
    assert "audio/ogg" in log_msg


def test_voice_frame_with_metadata():
    """Test VoiceFrame with metadata."""
    metadata = {"source": "voice_message", "timestamp": 123}
    frame = VoiceFrame(content=b"data", duration=30, mime_type="audio/ogg", metadata=metadata)
    assert frame.metadata == metadata


# StickerFrame Tests
def test_sticker_frame_valid():
    """Test StickerFrame with valid content."""
    content = b"sticker data"
    emoji = "😀"
    set_name = "test_set"
    frame = StickerFrame(content=content, emoji=emoji, set_name=set_name)
    assert frame.content == content
    assert frame.emoji == emoji
    assert frame.set_name == set_name


def test_sticker_frame_invalid_content():
    """Test StickerFrame with invalid content type."""
    with pytest.raises(TypeError, match="content must be bytes"):
        StickerFrame(content="not bytes", emoji="😀", set_name="test_set")


def test_sticker_frame_invalid_emoji():
    """Test StickerFrame with invalid emoji type."""
    with pytest.raises(TypeError, match="emoji must be a string"):
        StickerFrame(content=b"data", emoji=123, set_name="test_set")


def test_sticker_frame_invalid_set_name():
    """Test StickerFrame with invalid set_name type."""
    with pytest.raises(TypeError, match="set_name must be a string"):
        StickerFrame(content=b"data", emoji="😀", set_name=123)


@patch('chronicler.frames.media.logger')
def test_sticker_frame_logging(mock_logger):
    """Test that StickerFrame creation is logged."""
    frame = StickerFrame(content=b"data", emoji="😀", set_name="test_set")
    
    # Verify debug log was called with correct message
    mock_logger.debug.assert_called_once()
    log_msg = mock_logger.debug.call_args[0][0]
    assert "StickerFrame" in log_msg
    assert "😀" in log_msg
    assert "test_set" in log_msg


def test_sticker_frame_with_metadata():
    """Test StickerFrame with metadata."""
    metadata = {"source": "sticker_pack", "timestamp": 123}
    frame = StickerFrame(content=b"data", emoji="😀", set_name="test_set", metadata=metadata)
    assert frame.metadata == metadata 