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