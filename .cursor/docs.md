# Chronicler Implementation Details

## Pipeline System

### Frame Classes

```python
class Frame:
    """Base class for all frames in the pipeline."""
    metadata: dict

class TextFrame(Frame):
    """Frame for text messages."""
    text: str

class ImageFrame(Frame):
    """Frame for images."""
    image: bytes
    size: tuple[int, int]
    format: str

class DocumentFrame(Frame):
    """Frame for files, audio, video, etc."""
    content: bytes
    filename: str
    mime_type: str
    caption: Optional[str]
```

### Pipeline Components

```python
class BaseProcessor:
    """Base class for all processors."""
    async def process_frame(self, frame: Frame) -> None: ...
    async def push_frame(self, frame: Frame) -> None: ...

class Pipeline:
    """Manages frame flow through processors."""
    def __init__(self, processors: List[BaseProcessor]): ...
    async def process_frame(self, frame: Frame) -> None: ...

class BaseTransport(BaseProcessor):
    """Base class for I/O handlers."""
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

## Storage System

### Message Format

Messages are stored in JSONL format:
```json
{
    "content": "Message text",
    "timestamp": "2024-01-06T12:00:00Z",
    "metadata": {
        "chat_id": 123456789,
        "sender_id": 987654321,
        "message_id": 456,
        "thread_id": 1,
        "thread_name": "General"
    },
    "attachments": [
        {
            "type": "image/jpeg",
            "filename": "photo.jpg",
            "path": "media/images/photo.jpg"
        }
    ]
}
```

### Directory Structure

```
storage_root/
├── topics/
│   └── topic_name/
│       ├── messages.jsonl
│       └── media/
│           ├── images/
│           │   └── photo.jpg
│           ├── documents/
│           │   └── doc.pdf
│           └── audio/
│               └── voice.ogg
└── .git/
```

## Telegram Integration

### Message Types

1. **Text Messages**
   - Content: Direct text
   - Metadata: Sender, chat, timestamps
   - Special: Reply info, forwarding info

2. **Images**
   - Content: Binary image data
   - Metadata: Size, format, caption
   - Storage: JPEG/PNG in images/

3. **Documents**
   - Content: Binary file data
   - Metadata: Filename, MIME type
   - Storage: Original format in documents/

4. **Audio/Voice**
   - Content: Binary audio data
   - Metadata: Duration, format
   - Storage: OGG/MP3 in audio/

### Metadata Handling

1. **Basic Metadata**
   ```python
   {
       'chat_id': int,
       'chat_title': str,
       'thread_id': Optional[int],
       'thread_name': Optional[str],
       'sender_id': int,
       'sender_name': str
   }
   ```

2. **Reply Information**
   ```python
   {
       'reply_to': {
           'message_id': int,
           'sender_id': int,
           'sender_name': str,
           'type': str,
           'date': str
       }
   }
   ```

3. **Forward Information**
   ```python
   {
       'forward_origin': {
           'type': str,
           'date': str,
           'sender': {
               'user_id': int,
               'username': str,
               'name': str
           }
       }
   }
   ```

## Testing

### Unit Tests

1. **Frame Tests**
   - Creation with valid data
   - Metadata handling
   - Type-specific attributes

2. **Pipeline Tests**
   - Processor chaining
   - Frame flow
   - Error handling

### Mock Tests

1. **Storage Tests**
   - Message serialization
   - File organization
   - Git operations

2. **Processor Tests**
   - Frame processing
   - State management
   - Error recovery

### Live Tests

1. **Telegram Tests**
   - Bot initialization
   - Message handling
   - Media downloads

2. **Integration Tests**
   - End-to-end flow
   - Real data handling
   - Performance metrics 