"""Tests for command frame classes."""
import pytest
from chronicler.frames.command import CommandFrame

def test_command_frame_valid():
    """Test valid CommandFrame initialization."""
    frame = CommandFrame(command="/test", args=["arg1", "arg2"])
    assert frame.command == "/test"
    assert frame.args == ["arg1", "arg2"]
    assert frame.metadata == {"type": "commandframe"}

def test_command_frame_minimal():
    """Test CommandFrame with minimal fields."""
    frame = CommandFrame(command="/test")
    assert frame.command == "/test"
    assert frame.args == []
    assert frame.metadata == {"type": "commandframe"}

def test_command_frame_normalization():
    """Test command string normalization."""
    frame = CommandFrame(command="/TEST", args=["ARG1"])
    assert frame.command == "/test"  # Should be lowercase
    assert frame.args == ["ARG1"]  # Args should not be modified

def test_command_frame_validation():
    """Test command validation."""
    # Test command without leading slash
    with pytest.raises(ValueError, match="Command must start with '/'"):
        CommandFrame(command="test")

    # Test None command
    with pytest.raises(TypeError, match="command must be a string"):
        CommandFrame(command=None)

    # Test non-string command
    with pytest.raises(TypeError, match="command must be a string"):
        CommandFrame(command=123)

def test_command_frame_args_validation():
    """Test args validation."""
    # Test None args
    with pytest.raises(ValueError, match="Args must not be None"):
        CommandFrame(command="/test", args=None)

    # Test non-string args
    with pytest.raises(TypeError, match="All command arguments must be strings"):
        CommandFrame(command="/test", args=[123])

    # Test mixed args
    with pytest.raises(TypeError, match="All command arguments must be strings"):
        CommandFrame(command="/test", args=["valid", 123, "also_valid"])

def test_command_frame_with_metadata():
    """Test CommandFrame with metadata."""
    metadata = {"chat_id": 123, "message_id": 456}
    frame = CommandFrame(command="/test", metadata=metadata)
    expected = metadata.copy()
    expected["type"] = "commandframe"
    assert frame.metadata == expected 