import pytest
from pathlib import Path
from datetime import datetime
import json
import logging

from chronicler.storage.interface import Message, Attachment
from chronicler.storage.messages import MessageStore

@pytest.fixture()
def temp_file(tmp_path):
    """Provides a temporary file for testing"""
    return tmp_path / "messages.jsonl"

@pytest.mark.unit
def test_serialize_basic_message(temp_file, caplog, test_log_level):
    """Test serializing a basic message"""
    caplog.set_level(test_log_level)
    message = Message(
        content="Test message",
        metadata={"type": "chat"},
        source="test",
        timestamp=datetime.fromisoformat("2024-01-01T12:00:00+00:00")
    )
    
    MessageStore.save_messages(temp_file, [message])
    content = temp_file.read_text()
    
    # Verify JSONL format
    data = json.loads(content.strip())
    assert data["content"] == "Test message"
    assert data["source"] == "test"
    assert data["metadata"]["type"] == "chat"
    assert data["timestamp"] == "2024-01-01T12:00:00+00:00"

def test_serialize_message_with_attachments(temp_file, caplog, test_log_level):
    """Test serializing message with attachments"""
    caplog.set_level(test_log_level)
    attachments = [
        Attachment(id="att1", type="image/jpeg", filename="test.jpg"),
        Attachment(id="att2", type="text/plain", filename="test.txt")
    ]
    
    message = Message(
        content="Message with attachments",
        metadata={"type": "media"},
        source="test",
        timestamp=datetime.utcnow(),
        attachments=attachments
    )
    
    MessageStore.save_messages(temp_file, [message])
    data = json.loads(temp_file.read_text().strip())
    
    assert len(data["attachments"]) == 2
    assert data["attachments"][0]["filename"] == "test.jpg"
    assert data["attachments"][1]["type"] == "text/plain"

def test_load_multiple_messages(temp_file, caplog, test_log_level):
    """Test loading multiple messages from file"""
    caplog.set_level(test_log_level)
    messages = [
        Message(
            content=f"Message {i}",
            metadata={"sequence": i},
            source="test",
            timestamp=datetime.utcnow()
        ) for i in range(3)
    ]
    
    # Save messages
    MessageStore.save_messages(temp_file, messages)
    
    # Load and verify
    loaded = MessageStore.load_messages(temp_file)
    assert len(loaded) == 3
    assert loaded[0].content == "Message 0"
    assert loaded[2].content == "Message 2"
    assert all(msg.source == "test" for msg in loaded)
    # Verify JSONL format - one JSON object per line
    lines = temp_file.read_text().strip().split('\n')
    assert len(lines) == 3
    assert all(json.loads(line) for line in lines)  # Each line should be valid JSON

def test_append_multiple_messages(temp_file, caplog, test_log_level):
    """Test appending multiple messages one by one"""
    caplog.set_level(test_log_level)
    messages = [
        Message(
            content=f"Message {i}",
            metadata={"sequence": i},
            source="test",
            timestamp=datetime.utcnow()
        ) for i in range(3)
    ]
    
    # Save all messages at once
    MessageStore.save_messages(temp_file, messages)
    
    # Verify
    loaded = MessageStore.load_messages(temp_file)
    assert len(loaded) == 3
    assert [msg.content for msg in loaded] == ["Message 0", "Message 1", "Message 2"]

def test_load_empty_file(temp_file, caplog, test_log_level):
    """Test loading from empty or non-existent file"""
    caplog.set_level(test_log_level)
    # Non-existent file
    assert MessageStore.load_messages(temp_file) == []
    
    # Empty file
    temp_file.touch()
    assert MessageStore.load_messages(temp_file) == []

def test_metadata_handling(temp_file, caplog, test_log_level):
    """Test handling of special metadata fields"""
    caplog.set_level(test_log_level)
    message = Message(
        content="Test",
        metadata={
            "custom": "value",
            "source": "should_not_override",
            "timestamp": "should_not_override"
        },
        source="real_source",
        timestamp=datetime.fromisoformat("2024-01-01T12:00:00+00:00")
    )
    
    MessageStore.save_messages(temp_file, [message])
    loaded = MessageStore.load_messages(temp_file)[0]
    
    assert loaded.source == "real_source"
    assert loaded.timestamp == datetime.fromisoformat("2024-01-01T12:00:00+00:00")
    assert loaded.metadata == {"custom": "value"}

def test_unicode_content(temp_file, caplog, test_log_level):
    """Test handling of unicode content"""
    caplog.set_level(test_log_level)
    message = Message(
        content="Hello 👋 World 🌍",
        metadata={},
        source="test",
        timestamp=datetime.utcnow()
    )
    
    MessageStore.save_messages(temp_file, [message])
    loaded = MessageStore.load_messages(temp_file)[0]
    
    assert loaded.content == "Hello 👋 World 🌍" 