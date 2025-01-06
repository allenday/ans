"""Unit tests for command frames."""
import pytest

from chronicler.frames import Frame, CommandFrame

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
    with pytest.raises(TypeError):
        CommandFrame(command="/test", args=[1, 2, 3], metadata={}) 