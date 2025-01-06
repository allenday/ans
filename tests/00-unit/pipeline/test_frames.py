"""Unit tests for Frame classes."""
import pytest
from chronicler.pipeline import Frame, TextFrame, ImageFrame, DocumentFrame, AudioFrame, VoiceFrame, StickerFrame

def test_text_frame_creation():
    """Test creating a TextFrame."""
    frame = TextFrame(text="test message", metadata={'key': 'value'})
    assert frame.text == "test message"
    assert frame.metadata['key'] == 'value'

def test_text_frame_validation():
    """Test TextFrame validation."""
    with pytest.raises(TypeError):
        TextFrame()  # text is required
    
    with pytest.raises(TypeError):
        TextFrame(metadata={'key': 'value'})  # text is required

def test_image_frame_creation():
    """Test creating an ImageFrame."""
    frame = ImageFrame(
        image=b"test_image_data",
        size=(100, 200),
        format="jpeg",
        metadata={'key': 'value'}
    )
    assert frame.image == b"test_image_data"
    assert frame.size == (100, 200)
    assert frame.format == "jpeg"
    assert frame.metadata['key'] == 'value'

def test_image_frame_validation():
    """Test ImageFrame validation."""
    with pytest.raises(TypeError):
        ImageFrame()  # required fields missing
    
    with pytest.raises(TypeError):
        ImageFrame(image=b"data")  # size and format required
    
    with pytest.raises(TypeError):
        ImageFrame(image=b"data", size=(100, 200))  # format required

def test_document_frame_creation():
    """Test creating a DocumentFrame."""
    frame = DocumentFrame(
        content=b"test_document_data",
        filename="test.txt",
        mime_type="text/plain",
        caption="Test Caption",
        metadata={'key': 'value'}
    )
    assert frame.content == b"test_document_data"
    assert frame.filename == "test.txt"
    assert frame.mime_type == "text/plain"
    assert frame.caption == "Test Caption"
    assert frame.metadata['key'] == 'value'

def test_document_frame_validation():
    """Test DocumentFrame validation."""
    with pytest.raises(TypeError):
        DocumentFrame()  # required fields missing
    
    with pytest.raises(TypeError):
        DocumentFrame(content=b"data")  # filename and mime_type required
    
    # Caption is optional
    frame = DocumentFrame(
        content=b"data",
        filename="test.txt",
        mime_type="text/plain"
    )
    assert frame.caption is None

def test_audio_frame_creation():
    """Test creating an AudioFrame."""
    frame = AudioFrame(
        audio=b"test_audio_data",
        duration=120,  # 2 minutes
        mime_type="audio/mp3",
        metadata={'key': 'value'}
    )
    assert frame.audio == b"test_audio_data"
    assert frame.duration == 120
    assert frame.mime_type == "audio/mp3"
    assert frame.metadata['key'] == 'value'

def test_audio_frame_validation():
    """Test AudioFrame validation."""
    with pytest.raises(TypeError):
        AudioFrame()  # required fields missing
    
    with pytest.raises(TypeError):
        AudioFrame(audio=b"data")  # duration and mime_type required
    
    with pytest.raises(TypeError):
        AudioFrame(audio=b"data", duration=120)  # mime_type required

def test_voice_frame_creation():
    """Test creating a VoiceFrame."""
    frame = VoiceFrame(
        audio=b"test_voice_data",
        duration=30,  # 30 seconds
        mime_type="audio/ogg",
        metadata={'key': 'value'}
    )
    assert frame.audio == b"test_voice_data"
    assert frame.duration == 30
    assert frame.mime_type == "audio/ogg"
    assert frame.metadata['key'] == 'value'

def test_voice_frame_validation():
    """Test VoiceFrame validation."""
    with pytest.raises(TypeError):
        VoiceFrame()  # required fields missing
    
    with pytest.raises(TypeError):
        VoiceFrame(audio=b"data")  # duration and mime_type required
    
    with pytest.raises(TypeError):
        VoiceFrame(audio=b"data", duration=30)  # mime_type required

def test_sticker_frame_creation():
    """Test creating a StickerFrame."""
    frame = StickerFrame(
        sticker=b"test_sticker_data",
        emoji="😀",
        set_name="TestSet",
        metadata={'key': 'value'}
    )
    assert frame.sticker == b"test_sticker_data"
    assert frame.emoji == "😀"
    assert frame.set_name == "TestSet"
    assert frame.metadata['key'] == 'value'

def test_sticker_frame_validation():
    """Test StickerFrame validation."""
    with pytest.raises(TypeError):
        StickerFrame()  # required fields missing
    
    with pytest.raises(TypeError):
        StickerFrame(sticker=b"data")  # emoji and set_name required
    
    with pytest.raises(TypeError):
        StickerFrame(sticker=b"data", emoji="😀")  # set_name required

def test_frame_metadata():
    """Test metadata handling for all frame types."""
    frames = [
        TextFrame(text="test", metadata={'key': 'value'}),
        ImageFrame(image=b"data", size=(100,100), format="jpeg", metadata={'key': 'value'}),
        DocumentFrame(content=b"data", filename="test.txt", mime_type="text/plain", metadata={'key': 'value'}),
        AudioFrame(audio=b"data", duration=120, mime_type="audio/mp3", metadata={'key': 'value'}),
        VoiceFrame(audio=b"data", duration=30, mime_type="audio/ogg", metadata={'key': 'value'}),
        StickerFrame(sticker=b"data", emoji="😀", set_name="TestSet", metadata={'key': 'value'})
    ]
    
    for frame in frames:
        assert frame.metadata['key'] == 'value'
        assert isinstance(frame.metadata, dict)

def test_frame_inheritance():
    """Test that all frame types inherit from Frame."""
    frames = [
        TextFrame(text="test"),
        ImageFrame(image=b"data", size=(100,100), format="jpeg"),
        DocumentFrame(content=b"data", filename="test.txt", mime_type="text/plain"),
        AudioFrame(audio=b"data", duration=120, mime_type="audio/mp3"),
        VoiceFrame(audio=b"data", duration=30, mime_type="audio/ogg"),
        StickerFrame(sticker=b"data", emoji="😀", set_name="TestSet")
    ]
    
    for frame in frames:
        assert isinstance(frame, Frame) 