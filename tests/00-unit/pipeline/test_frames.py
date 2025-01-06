"""Unit tests for Frame classes."""
import pytest
from chronicler.pipeline import Frame, TextFrame, ImageFrame, DocumentFrame

def test_text_frame_creation():
    """Test creating a TextFrame."""
    frame = TextFrame(text="test message", metadata={'key': 'value'})
    assert frame.text == "test message"
    assert frame.metadata['key'] == 'value'

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