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
    """Test that Frame metadata defaults to empty dict."""
    frame = TestFrame()
    assert frame.metadata == {}


def test_frame_metadata_custom():
    """Test Frame with custom metadata."""
    metadata = {"key": "value", "number": 42}
    frame = TestFrame(metadata=metadata)
    assert frame.metadata == metadata


def test_frame_text_default():
    """Test that Frame text defaults to None."""
    frame = TestFrame()
    assert frame.text is None


def test_frame_text_custom():
    """Test Frame with custom text."""
    text = "Test text"
    frame = TestFrame(text=text)
    assert frame.text == text


@patch('chronicler.frames.base.logger')
def test_frame_logging(mock_logger):
    """Test that Frame creation is logged."""
    metadata = {"test": "data"}
    frame = TestFrame(metadata=metadata)
    
    # Verify debug log was called with correct message
    mock_logger.debug.assert_called_once()
    log_msg = mock_logger.debug.call_args[0][0]
    assert "TestFrame" in log_msg
    assert str(metadata) in log_msg


def test_frame_metadata_mutation():
    """Test that Frame metadata can be modified after creation."""
    frame = TestFrame()
    frame.metadata["new_key"] = "new_value"
    assert frame.metadata["new_key"] == "new_value"


def test_frame_text_mutation():
    """Test that Frame text can be modified after creation."""
    frame = TestFrame()
    frame.text = "New text"
    assert frame.text == "New text" 