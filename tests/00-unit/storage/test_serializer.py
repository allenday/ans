import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import yaml
import json
from datetime import datetime, timezone

from chronicler.storage.serializer import MessageSerializer
from chronicler.storage.interface import Message, Attachment

@pytest.fixture
def serializer():
    return MessageSerializer()

@pytest.fixture
def message():
    return Message(
        content="Test message",
        source="test",
        timestamp=datetime.now(timezone.utc),
        metadata={'key': 'value'}
    )

@pytest.fixture
def attachments():
    return [
        {'id': 'att1', 'type': 'image/jpeg', 'original_name': 'image.jpg'},
        {'id': 'att2', 'type': 'application/pdf', 'original_name': 'doc.pdf'}
    ]

@pytest.mark.parametrize("content, expected_length", [
    ("", 268),
    ("Normal content", 282),
    (b"Non-UTF-8 content \x80\x81", 288),
    ("Large content" * 1000, 13268)
])
def test_serialize_message(serializer, message, attachments, content, expected_length):
    message.content = content
    serialized = serializer.serialize_message(message, attachments)
    assert len(serialized) == expected_length

@pytest.mark.parametrize("metadata_content, expected_keys", [
    ("user_id: test_user\ntopics: {}", 2),
    ("", 0),
    ("invalid_yaml: [", 0)
])
def test_read_metadata(serializer, tmp_path, metadata_content, expected_keys):
    metadata_path = tmp_path / "metadata.yaml"
    metadata_path.write_text(metadata_content)
    metadata = serializer.read_metadata(metadata_path)
    assert len(metadata) == expected_keys

@pytest.mark.parametrize("metadata, expected_keys", [
    ({'user_id': 'test_user', 'topics': {}}, 2),
    ({}, 0)
])
def test_write_metadata(serializer, tmp_path, metadata, expected_keys):
    metadata_path = tmp_path / "metadata.yaml"
    serializer.write_metadata(metadata_path, metadata)
    with open(metadata_path) as f:
        written_metadata = yaml.safe_load(f)
    assert len(written_metadata) == expected_keys 

def test_serialize_message_error(serializer, message, attachments):
    """Test error handling in message serialization."""
    # Make message.content a type that can't be JSON serialized
    message.content = object()
    
    with pytest.raises(Exception):
        serializer.serialize_message(message, attachments)

def test_serialize_message_with_binary_content(serializer, message, attachments):
    """Test serializing message with binary content."""
    message.content = b"Binary \x80\x81 content"
    serialized = serializer.serialize_message(message, attachments)
    
    # Verify content was properly decoded
    data = json.loads(serialized)
    assert "Binary" in data['content']
    assert "content" in data['content']

def test_serialize_message_with_none_content(serializer, message, attachments):
    """Test serializing message with None content."""
    message.content = None
    serialized = serializer.serialize_message(message, attachments)
    
    # Verify content is None in serialized data
    data = json.loads(serialized)
    assert data['content'] is None

def test_read_metadata_file_error(serializer, tmp_path):
    """Test error handling when reading metadata file."""
    metadata_path = tmp_path / "metadata.yaml"
    
    # Create a file that can't be read
    metadata_path.touch(mode=0o000)
    
    with pytest.raises(Exception):
        serializer.read_metadata(metadata_path)

def test_write_metadata_file_error(serializer, tmp_path):
    """Test error handling when writing metadata file."""
    metadata_path = tmp_path / "metadata.yaml"
    metadata = {'key': 'value'}
    
    # Create a directory instead of a file to cause write error
    metadata_path.mkdir()
    
    with pytest.raises(Exception):
        serializer.write_metadata(metadata_path, metadata)

def test_write_metadata_yaml_error(serializer, tmp_path):
    """Test error handling with non-serializable metadata."""
    metadata_path = tmp_path / "metadata.yaml"
    # Create a circular reference that can't be serialized
    metadata = {}
    metadata['self'] = metadata

    with pytest.raises(ValueError, match="Invalid metadata structure"):
        serializer.write_metadata(metadata_path, metadata)

def test_update_topic_metadata_new_source(serializer):
    """Test updating topic metadata with new source."""
    metadata = {}
    topic_name = "Test Topic"
    topic_id = "test_topic"
    source = "test_source"
    group_id = "test_group"
    topic_metadata = {'key': 'value'}
    
    result = serializer.update_topic_metadata(metadata, topic_name, topic_id, source, group_id, topic_metadata)
    
    assert 'sources' in result
    assert source in result['sources']
    assert group_id in result['sources'][source]['groups']
    assert topic_id in result['sources'][source]['groups'][group_id]['topics']
    assert result['sources'][source]['groups'][group_id]['topics'][topic_id]['metadata'] == topic_metadata

def test_update_topic_metadata_existing_source(serializer):
    """Test updating topic metadata with existing source."""
    metadata = {
        'sources': {
            'test_source': {
                'groups': {}
            }
        }
    }
    topic_name = "Test Topic"
    topic_id = "test_topic"
    source = "test_source"
    group_id = "test_group"
    topic_metadata = {'key': 'value'}
    
    result = serializer.update_topic_metadata(metadata, topic_name, topic_id, source, group_id, topic_metadata)
    
    assert group_id in result['sources'][source]['groups']
    assert topic_id in result['sources'][source]['groups'][group_id]['topics']

def test_update_topic_metadata_existing_group(serializer):
    """Test updating topic metadata with existing group."""
    metadata = {
        'sources': {
            'test_source': {
                'groups': {
                    'test_group': {
                        'name': 'Test Group',
                        'topics': {}
                    }
                }
            }
        }
    }
    topic_name = "Test Topic"
    topic_id = "test_topic"
    source = "test_source"
    group_id = "test_group"
    topic_metadata = {'key': 'value'}
    
    result = serializer.update_topic_metadata(metadata, topic_name, topic_id, source, group_id, topic_metadata)
    
    assert topic_id in result['sources'][source]['groups'][group_id]['topics']
    assert result['sources'][source]['groups'][group_id]['name'] == 'Test Group'

def test_update_topic_metadata_error(serializer):
    """Test error handling in topic metadata update."""
    metadata = None  # Invalid metadata
    topic_name = "Test Topic"
    topic_id = "test_topic"
    source = "test_source"
    group_id = "test_group"
    topic_metadata = {'key': 'value'}
    
    with pytest.raises(Exception):
        serializer.update_topic_metadata(metadata, topic_name, topic_id, source, group_id, topic_metadata) 