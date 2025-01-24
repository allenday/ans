"""Unit tests for base Frame class."""
import pytest
from unittest.mock import patch
from chronicler.frames import Frame
from dataclasses import dataclass


@dataclass
class TestFrame(Frame):
    """Test implementation of abstract Frame class."""
    pass


def test_frame_metadata_default():
    """Test that Frame metadata defaults to empty dict with type."""
    frame = TestFrame()
    assert frame.metadata == {"type": "testframe"}


def test_frame_metadata_custom():
    """Test Frame with custom metadata."""
    metadata = {"test": "value"}
    frame = TestFrame(metadata=metadata)
    expected = metadata.copy()
    expected["type"] = "testframe"
    assert frame.metadata == expected


def test_frame_text_default():
    """Test that Frame text defaults to None."""
    frame = TestFrame()
    assert frame.content is None


def test_frame_text_custom():
    """Test Frame with custom text."""
    text = "test text"
    frame = TestFrame(content=text)
    assert frame.content == text


@patch('chronicler.frames.base.logger')
def test_frame_logging(mock_logger):
    """Test that Frame creation is logged."""
    frame = TestFrame()
    # Basic initialization should not raise any errors
    
    # Verify debug log was called with correct message
    mock_logger.debug.assert_called_once()
    log_msg = mock_logger.debug.call_args[0][0]
    assert "TestFrame" in log_msg
    assert str(frame.metadata) in log_msg


def test_frame_metadata_mutation():
    """Test that Frame metadata can be updated."""
    frame = TestFrame()
    frame.metadata["new_key"] = "value"
    assert frame.metadata["new_key"] == "value"


def test_frame_text_mutation():
    """Test that Frame text can be updated."""
    frame = TestFrame()
    frame.text = "new text"
    assert frame.text == "new text" 