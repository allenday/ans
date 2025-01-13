"""Unit tests for filesystem storage."""
import pytest
from pathlib import Path
import os
from unittest.mock import patch, mock_open, MagicMock

from chronicler.storage.filesystem import FileSystemStorage

@pytest.fixture
def fs_storage(tmp_path):
    """Create a FileSystemStorage instance with a temporary base path."""
    return FileSystemStorage(tmp_path)

def test_init(tmp_path):
    """Test FileSystemStorage initialization."""
    fs = FileSystemStorage(tmp_path)
    assert fs.base_path == tmp_path

def test_get_topic_path(fs_storage):
    """Test topic path generation and creation."""
    # Test normal path creation
    path = fs_storage.get_topic_path("telegram", "123", "topic1")
    assert path == fs_storage.base_path / "telegram" / "123" / "topic1"
    assert path.exists()
    assert path.is_dir()

    # Test path with special characters
    path = fs_storage.get_topic_path("telegram", "group#123", "topic/with/slashes")
    assert path == fs_storage.base_path / "telegram" / "group#123" / "topic/with/slashes"
    assert path.exists()
    assert path.is_dir()

def test_get_topic_path_error(fs_storage, monkeypatch):
    """Test topic path error handling."""
    def mock_mkdir(*args, **kwargs):
        raise PermissionError("Access denied")
    
    monkeypatch.setattr(Path, "mkdir", mock_mkdir)
    
    with pytest.raises(PermissionError):
        fs_storage.get_topic_path("telegram", "123", "topic1")

def test_get_attachment_path(fs_storage):
    """Test attachment path generation and creation."""
    topic_path = fs_storage.base_path / "test_topic"
    
    # Test simple attachment path
    path = fs_storage.get_attachment_path(topic_path, "photo", "image.jpg")
    assert path == topic_path / "attachments" / "photo" / "image.jpg"
    assert path.parent.exists()
    assert path.parent.is_dir()
    
    # Test nested attachment path
    path = fs_storage.get_attachment_path(topic_path, "sticker", "pack_name", "sticker.webp")
    assert path == topic_path / "attachments" / "sticker" / "pack_name" / "sticker.webp"
    assert path.parent.exists()
    assert path.parent.is_dir()

def test_get_attachment_path_error(fs_storage, monkeypatch):
    """Test attachment path error handling."""
    def mock_mkdir(*args, **kwargs):
        raise PermissionError("Access denied")
    
    monkeypatch.setattr(Path, "mkdir", mock_mkdir)
    
    topic_path = fs_storage.base_path / "test_topic"
    with pytest.raises(PermissionError):
        fs_storage.get_attachment_path(topic_path, "photo", "image.jpg")

def test_save_file(fs_storage):
    """Test file saving functionality."""
    test_path = fs_storage.base_path / "test.txt"
    test_content = b"Hello, World!"
    
    fs_storage.save_file(test_path, test_content)
    
    assert test_path.exists()
    assert test_path.read_bytes() == test_content

def test_save_file_error(fs_storage):
    """Test file saving error handling."""
    test_path = fs_storage.base_path / "test.txt"
    test_content = b"Hello, World!"
    
    # Test write permission error
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = PermissionError("Access denied")
        with pytest.raises(PermissionError):
            fs_storage.save_file(test_path, test_content)
    
    # Test disk full error
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.return_value.write.side_effect = OSError("No space left on device")
        with pytest.raises(OSError):
            fs_storage.save_file(test_path, test_content)

def test_append_jsonl(fs_storage):
    """Test JSONL file appending functionality."""
    test_path = fs_storage.base_path / "test.jsonl"
    test_content = '{"key": "value"}'
    
    # Test appending to new file
    fs_storage.append_jsonl(test_path, test_content)
    assert test_path.exists()
    with open(test_path) as f:
        assert f.read().strip() == test_content
    
    # Test appending to existing file
    second_content = '{"key2": "value2"}'
    fs_storage.append_jsonl(test_path, second_content)
    with open(test_path) as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert lines[0].strip() == test_content
        assert lines[1].strip() == second_content

def test_append_jsonl_error(fs_storage):
    """Test JSONL file appending error handling."""
    test_path = fs_storage.base_path / "test.jsonl"
    test_content = '{"key": "value"}'
    
    # Test write permission error
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = PermissionError("Access denied")
        with pytest.raises(PermissionError):
            fs_storage.append_jsonl(test_path, test_content)
    
    # Test disk full error
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.return_value.write.side_effect = OSError("No space left on device")
        with pytest.raises(OSError):
            fs_storage.append_jsonl(test_path, test_content)

def test_unicode_handling(fs_storage):
    """Test handling of Unicode content in files."""
    test_path = fs_storage.base_path / "unicode.jsonl"
    test_content = '{"text": "Hello, 世界! 🌍"}'
    
    fs_storage.append_jsonl(test_path, test_content)
    
    with open(test_path, encoding='utf-8') as f:
        assert f.read().strip() == test_content 