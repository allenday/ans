"""Tests for message serializer."""
import pytest
from pathlib import Path
from datetime import datetime
import json

from chronicler.storage.interface import Message
from chronicler.storage.serializer import MessageSerializer

@pytest.fixture
def serializer():
    """Create a message serializer."""
    return MessageSerializer()

def test_serialize_message(serializer):
    """Test serializing a message."""
    message = Message(
        content="Test message",
        source="test",
        timestamp=datetime(2024, 1, 1, 12, 0),
        metadata={"key": "value"},
        id="msg_123"
    )
    
    result = serializer.serialize_message(message)
    data = json.loads(result)
    
    assert data["content"] == "Test message"
    assert data["source"] == "test"
    assert data["timestamp"] == "2024-01-01T12:00:00"
    assert data["metadata"] == {"key": "value"}
    assert data["id"] == "msg_123"

def test_serialize_message_with_binary_content(serializer):
    """Test serializing a message with binary content."""
    message = Message(
        content=b"Binary content",
        source="test",
        timestamp=datetime(2024, 1, 1, 12, 0),
        metadata={"key": "value"},
        id="msg_123"
    )
    
    result = serializer.serialize_message(message)
    data = json.loads(result)
    
    assert data["content"] == "Binary content"
    assert data["source"] == "test"
    assert data["timestamp"] == "2024-01-01T12:00:00"
    assert data["metadata"] == {"key": "value"}
    assert data["id"] == "msg_123"

def test_read_metadata(serializer, tmp_path):
    """Test reading metadata from file."""
    metadata_file = tmp_path / "metadata.json"
    test_metadata = {
        "key": "value",
        "nested": {
            "key": "value"
        }
    }
    
    # Write test metadata
    with metadata_file.open("w") as f:
        json.dump(test_metadata, f)
        
    # Read metadata
    result = serializer.read_metadata(metadata_file)
    assert result == test_metadata

def test_read_metadata_missing_file(serializer, tmp_path):
    """Test reading metadata from missing file."""
    metadata_file = tmp_path / "missing.json"
    result = serializer.read_metadata(metadata_file)
    assert result == {}

def test_write_metadata(serializer, tmp_path):
    """Test writing metadata to file."""
    metadata_file = tmp_path / "metadata.json"
    test_metadata = {
        "key": "value",
        "nested": {
            "key": "value"
        }
    }
    
    # Write metadata
    serializer.write_metadata(metadata_file, test_metadata)
    
    # Verify metadata was written
    with metadata_file.open() as f:
        result = json.load(f)
        assert result == test_metadata

def test_write_metadata_invalid_structure(serializer, tmp_path):
    """Test writing invalid metadata structure."""
    metadata_file = tmp_path / "metadata.json"
    
    # Create circular reference
    test_metadata = {}
    test_metadata["self"] = test_metadata
    
    # Verify error is raised
    with pytest.raises(ValueError, match="Invalid metadata structure"):
        serializer.write_metadata(metadata_file, test_metadata) 