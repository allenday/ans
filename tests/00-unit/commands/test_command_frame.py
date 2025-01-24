"""Tests for command frames."""
import pytest
from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame

def test_command_frame_init():
    """Test command frame initialization."""
    frame = CommandFrame(
        command="/test",
        args=["arg1", "arg2"],
        metadata={"key": "value"}
    )
    assert frame.command == "/test"
    assert frame.args == ["arg1", "arg2"]
    assert frame.metadata == {"key": "value", "type": "commandframe"}

def test_command_frame_basic():
    """Test basic command frame creation."""
    frame = CommandFrame(command="/test", metadata={})
    assert isinstance(frame, Frame)
    assert frame.command == "/test"
    assert frame.args == []

def test_command_frame_with_args():
    """Test command frame with arguments."""
    frame = CommandFrame(command="/test", args=["arg1", "arg2"], metadata={})
    assert frame.command == "/test"
    assert frame.args == ["arg1", "arg2"]

def test_command_frame_with_metadata():
    """Test command frame with metadata."""
    metadata = {"user_id": 123, "chat_id": 456}
    frame = CommandFrame(command="/test", metadata=metadata)
    assert frame.metadata == metadata

def test_command_frame_command_validation():
    """Test command validation."""
    with pytest.raises(ValueError):
        CommandFrame(command="invalid", metadata={})

def test_command_frame_args_validation():
    """Test args validation."""
    # Test None args
    with pytest.raises(ValueError, match="Args must not be None"):
        CommandFrame(command="/test", args=None)
        
    # Test non-string args
    with pytest.raises(TypeError, match="All command arguments must be strings"):
        CommandFrame(command="/test", args=[123])

def test_command_frame_validation():
    """Test command frame validation."""
    # Test invalid command format
    with pytest.raises(ValueError, match="Command must start with '/'"):
        CommandFrame(command="test", args=["arg1"])
        
    # Test invalid args type
    with pytest.raises(TypeError, match="All command arguments must be strings"):
        CommandFrame(command="/test", args=[123])