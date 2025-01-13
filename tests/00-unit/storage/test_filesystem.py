"""Unit tests for filesystem storage."""
import pytest
from pathlib import Path
import os
from unittest.mock import patch, mock_open, MagicMock
import psutil

from chronicler.storage.filesystem import FileSystemStorage

@pytest.fixture
def mock_process():
    """Mock psutil.Process for memory metrics."""
    with patch('psutil.Process') as mock:
        memory_info = MagicMock()
        memory_info.rss = 1024 * 1024  # 1MB in bytes
        mock.return_value.memory_info.return_value = memory_info
        yield mock

@pytest.fixture
def fs_storage(tmp_path, mock_process):
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

def test_save_file_error(fs_storage, mock_process):
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

def test_append_jsonl_error(fs_storage, mock_process):
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

def test_special_characters_in_paths(fs_storage):
    """Test handling of special characters in paths."""
    # Test spaces and special characters
    path = fs_storage.get_topic_path("telegram", "group with spaces", "topic#1")
    assert path.exists()
    assert path.is_dir()
    
    # Test non-ASCII characters
    path = fs_storage.get_topic_path("telegram", "группа", "主题")
    assert path.exists()
    assert path.is_dir()
    
    # Test special filesystem characters
    path = fs_storage.get_topic_path("telegram", "group*?", "topic<>|")
    assert path.exists()
    assert path.is_dir()

def test_long_paths(fs_storage):
    """Test handling of very long paths."""
    long_name = "x" * 200  # Create a very long name
    
    # Test long topic path
    path = fs_storage.get_topic_path("telegram", "group", long_name)
    assert path.exists()
    assert path.is_dir()
    
    # Test long attachment path
    topic_path = fs_storage.base_path / "test_topic"
    path = fs_storage.get_attachment_path(topic_path, "photo", long_name)
    assert path.parent.exists()
    assert path.parent.is_dir()

def test_relative_vs_absolute_paths(fs_storage):
    """Test handling of relative and absolute paths."""
    # Test with relative path
    rel_path = Path("test_topic")
    abs_path = fs_storage.base_path / rel_path

    # Both should work the same
    path1 = fs_storage.get_attachment_path(rel_path, "photo", "image.jpg")
    path2 = fs_storage.get_attachment_path(abs_path, "photo", "image.jpg")

    # Compare path strings after removing base path
    path1_str = str(path1).replace(str(fs_storage.base_path), "").lstrip("/")
    path2_str = str(path2).replace(str(fs_storage.base_path), "").lstrip("/")
    assert path1_str == path2_str

@pytest.mark.asyncio
async def test_concurrent_file_operations(fs_storage):
    """Test concurrent file operations."""
    import asyncio
    
    test_path = fs_storage.base_path / "concurrent.txt"
    test_content = b"test content"
    
    # Create multiple concurrent save operations
    tasks = []
    for i in range(5):
        tasks.append(asyncio.create_task(
            asyncio.to_thread(fs_storage.save_file, test_path, test_content)
        ))
    
    # Should complete without errors
    await asyncio.gather(*tasks)
    
    # Verify file exists and has correct content
    assert test_path.exists()
    assert test_path.read_bytes() == test_content

def test_large_file_handling(fs_storage):
    """Test handling of large files."""
    test_path = fs_storage.base_path / "large.bin"
    
    # Create 10MB of random data
    import os
    test_content = os.urandom(10 * 1024 * 1024)
    
    # Save and verify
    fs_storage.save_file(test_path, test_content)
    assert test_path.exists()
    assert test_path.stat().st_size == len(test_content)
    assert test_path.read_bytes() == test_content

def test_file_permissions(fs_storage, tmp_path):
    """Test file permission handling."""
    import os
    import stat
    
    # Create a read-only directory
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)
    
    try:
        # Attempt to create a file in read-only directory
        test_path = readonly_dir / "test.txt"
        with pytest.raises(PermissionError):
            fs_storage.save_file(test_path, b"test")
    finally:
        # Restore permissions for cleanup
        os.chmod(readonly_dir, stat.S_IRWXU)

def test_invalid_path_characters(fs_storage):
    """Test handling of invalid path characters."""
    import platform
    
    # Different invalid characters for different OS
    if platform.system() == "Windows":
        invalid_chars = '<>:"|?*'
    else:
        invalid_chars = '\0'  # Null byte is invalid on Unix
    
    for char in invalid_chars:
        with pytest.raises(Exception):
            fs_storage.get_topic_path("telegram", f"group{char}", "topic")

def test_path_too_long(fs_storage):
    """Test handling of paths that exceed system limits."""
    # Create an extremely long path (typically >32K chars on Unix, >260 on Windows)
    very_long_name = "x" * 32768
    
    with pytest.raises(Exception):
        fs_storage.get_topic_path("telegram", very_long_name, very_long_name)

def test_disk_io_errors(fs_storage, mock_process):
    """Test handling of various disk I/O errors."""
    test_path = fs_storage.base_path / "test.txt"
    test_data = b"test data"

    # Test disk full
    def mock_write_full(*args, **kwargs):
        raise OSError(28, "No space left on device")

    # Mock the file context manager
    mock_file = MagicMock()
    mock_file.__enter__ = MagicMock(return_value=mock_file)
    mock_file.__exit__ = MagicMock(return_value=None)
    mock_file.write.side_effect = mock_write_full

    mock_open = MagicMock(return_value=mock_file)
    with patch("builtins.open", mock_open):
        with pytest.raises(OSError, match="No space left on device"):
            fs_storage.save_file(test_path, test_data)

def test_race_conditions(fs_storage, monkeypatch):
    """Test handling of race conditions in file operations."""
    test_path = fs_storage.base_path / "race.txt"
    
    # Simulate directory disappearing after check but before write
    orig_exists = Path.exists
    orig_open = open
    
    def mock_exists(self):
        if str(self) == str(test_path.parent):
            return True
        return orig_exists(self)
    
    def mock_open(*args, **kwargs):
        if str(args[0]) == str(test_path):
            raise FileNotFoundError("Directory disappeared")
        return orig_open(*args, **kwargs)
    
    monkeypatch.setattr(Path, "exists", mock_exists)
    monkeypatch.setattr("builtins.open", mock_open)
    
    with pytest.raises(FileNotFoundError):
        fs_storage.save_file(test_path, b"test") 