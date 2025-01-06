"""Unit tests for CommandFrame."""
import pytest
from chronicler.commands.frames import CommandFrame

def test_command_frame_basic():
    """Test basic CommandFrame creation."""
    frame = CommandFrame(
        command="/test",
        args=[],
        metadata={}
    )
    assert frame.command == "/test"
    assert frame.args == []
    assert frame.metadata == {}

def test_command_frame_with_args():
    """Test CommandFrame with arguments."""
    frame = CommandFrame(
        command="/test",
        args=["arg1", "arg2"],
        metadata={}
    )
    assert frame.command == "/test"
    assert frame.args == ["arg1", "arg2"]
    assert len(frame.args) == 2

def test_command_frame_with_metadata():
    """Test CommandFrame with metadata."""
    metadata = {'key': 'value', 'number': 123}
    frame = CommandFrame(
        command="/test",
        args=[],
        metadata=metadata
    )
    assert frame.metadata == metadata
    assert frame.metadata['key'] == 'value'
    assert frame.metadata['number'] == 123

def test_command_frame_command_validation():
    """Test command validation."""
    # Commands should start with /
    with pytest.raises(ValueError):
        CommandFrame(command="test", args=[], metadata={})
    
    # Commands should be lowercase
    frame = CommandFrame(command="/TEST", args=[], metadata={})
    assert frame.command == "/test"

def test_command_frame_args_validation():
    """Test argument validation."""
    # Args should be strings
    with pytest.raises(TypeError):
        CommandFrame(command="/test", args=[123], metadata={})
    
    # Args should not be None
    with pytest.raises(ValueError):
        CommandFrame(command="/test", args=None, metadata={}) 