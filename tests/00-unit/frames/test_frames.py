"""Tests for frame validation and functionality."""
import pytest
from unittest.mock import Mock
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.frames.command import CommandFrame
from chronicler.frames.base import Frame

@pytest.mark.asyncio
async def test_frame_metadata_validation():
    """Test frame metadata validation."""
    # Test None metadata
    frame = TextFrame(content="test")  # Should initialize with default metadata
    assert frame.metadata == {"type": "textframe"}

    # Test empty metadata
    frame = TextFrame(content="test", metadata={})
    assert frame.metadata == {"type": "textframe"}

    # Test custom metadata
    metadata = {"chat_id": 123}
    frame = TextFrame(content="test", metadata=metadata)
    expected = metadata.copy()
    expected["type"] = "textframe"
    assert frame.metadata == expected

@pytest.mark.asyncio
async def test_text_frame_validation():
    """Test text frame validation."""
    # Test None content
    with pytest.raises(TypeError, match="content must be a string"):
        TextFrame(content=None)

    # Test invalid content type
    with pytest.raises(TypeError, match="content must be a string"):
        TextFrame(content=123)

@pytest.mark.asyncio
async def test_image_frame_validation():
    """Test image frame validation."""
    # Test None content
    with pytest.raises(TypeError, match="content must be bytes"):
        ImageFrame(content=None)

    # Test invalid content type
    with pytest.raises(TypeError, match="content must be bytes"):
        ImageFrame(content="not bytes")

    # Test invalid size
    with pytest.raises(TypeError, match="size must be a tuple of two integers"):
        ImageFrame(content=b"test", size=(1, 2, 3))

    # Test invalid format
    with pytest.raises(TypeError, match="format must be a string"):
        ImageFrame(content=b"test", format=123)

@pytest.mark.asyncio
async def test_command_frame_validation():
    """Test command frame validation."""
    # Test command without leading slash
    with pytest.raises(ValueError, match="Command must start with '/'"):
        CommandFrame(command="test", args=[])

    # Test None command
    with pytest.raises(TypeError, match="command must be a string"):
        CommandFrame(command=None, args=[])

    # Test None args
    with pytest.raises(ValueError, match="Args must not be None"):
        CommandFrame(command="/test", args=None)

    # Test non-string args
    with pytest.raises(TypeError, match="All command arguments must be strings"):
        CommandFrame(command="/test", args=[123])

@pytest.mark.asyncio
async def test_frame_metadata_immutability():
    """Test that frame metadata can be updated."""
    frame = TextFrame(content="test", metadata={"chat_id": 123})
    
    # Update metadata
    frame.metadata["new_key"] = "value"
    assert frame.metadata["new_key"] == "value"
    assert frame.metadata["chat_id"] == 123
    assert frame.metadata["type"] == "textframe"

@pytest.mark.asyncio
async def test_frame_content_access():
    """Test that frame content can be accessed and modified."""
    frame = TextFrame(content="test")
    
    # Content should be accessible
    assert frame.content == "test"
    
    # Content should be modifiable
    frame.content = "new value"
    assert frame.content == "new value" 