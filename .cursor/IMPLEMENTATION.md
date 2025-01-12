# Chronicler Implementation Details
> See [ARCHITECTURE.md](.cursor/ARCHITECTURE.md) for system design, [CONVENTIONS.md](.cursor/CONVENTIONS.md) for standards

## Pipeline Implementation

### Frame Classes
```python
class Frame:
    """Base class for all frames in the pipeline."""
    metadata: dict
    id: str  # Unique frame identifier
    timestamp: datetime
    source: str  # Origin transport identifier

class TextFrame(Frame):
    """Frame for text messages."""
    text: str
    format: Optional[str] = None  # For markdown/html/etc

class ImageFrame(Frame):
    """Frame for images."""
    image: bytes
    size: tuple[int, int]
    format: str  # Enforced JPEG/PNG only
    thumbnail: Optional[bytes] = None

class DocumentFrame(Frame):
    """Frame for files, audio, video, etc."""
    content: bytes
    filename: str
    mime_type: str
    caption: Optional[str]
    size: int  # File size in bytes
    hash: str  # Content hash for deduplication
```

### Core Components
```python
class BaseProcessor:
    """Base class for all processors."""
    name: str  # Processor identifier
    config: dict  # Runtime configuration
    metrics: dict  # Performance metrics

    async def process_frame(self, frame: Frame) -> None: ...
    async def push_frame(self, frame: Frame) -> None: ...
    async def initialize(self) -> None: ...  # Setup hook
    async def cleanup(self) -> None: ...     # Cleanup hook

class Pipeline:
    """Manages frame flow through processors."""
    def __init__(self, processors: List[BaseProcessor]): ...
    async def process_frame(self, frame: Frame) -> None: ...
    async def start(self) -> None: ...  # Initialize all processors
    async def stop(self) -> None: ...   # Cleanup all processors
    def add_processor(self, processor: BaseProcessor, index: int) -> None: ...
    def remove_processor(self, name: str) -> None: ...

class BaseTransport(BaseProcessor):
    """Base class for I/O handlers."""
    async def start(self) -> None: ...  # Connect to external system
    async def stop(self) -> None: ...   # Disconnect cleanly
    async def health_check(self) -> bool: ...  # Connection status
```

## Storage Implementation

### Message Schema
```json
{
    "id": "msg_uuid4",
    "content": "Message text",
    "timestamp": "2024-01-06T12:00:00Z",
    "metadata": {
        "chat_id": 123456789,
        "sender_id": 987654321,
        "message_id": 456,
        "thread_id": 1,
        "thread_name": "General",
        "source": "telegram",
        "processed_by": ["filter", "transform", "store"]
    },
    "attachments": [
        {
            "id": "att_uuid4",
            "type": "image/jpeg",
            "filename": "photo.jpg",
            "path": "media/images/photo.jpg",
            "size": 102400,
            "hash": "sha256_hash",
            "metadata": {
                "width": 1920,
                "height": 1080,
                "has_thumbnail": true
            }
        }
    ],
    "version": "1.0"
}
```

### Storage Structure
```
storage_root/
├── topics/
│   └── topic_name/
│       ├── messages.jsonl       # Append-only message log
│       ├── messages.index      # Message search index
│       ├── attachments.index   # Media file index
│       └── media/
│           ├── images/         # JPEG/PNG only
│           ├── documents/      # General files
│           └── audio/          # OGG/MP3 only
└── .git/                      # Version control
```

## Transport Implementation

### Message Types
1. **Text**
   - Content: Direct text
   - Metadata: Sender, chat, timestamps
   - Special: Reply info, forwarding info
   - Formats: Plain, Markdown, HTML
   - Size limits: Platform-specific

2. **Media**
   - Images: JPEG/PNG with dimensions
   - Documents: Original format with MIME type
   - Audio: OGG/MP3 with duration
   - Size limits: Per type enforcement
   - Deduplication: Content-based

### Metadata Schemas
1. **Base Schema**
   ```python
   {
       'id': str,              # UUID4
       'chat_id': int,
       'chat_title': str,
       'thread_id': Optional[int],
       'thread_name': Optional[str],
       'sender_id': int,
       'sender_name': str,
       'timestamp': datetime,
       'source': str,          # Platform identifier
       'version': str          # Schema version
   }
   ```

2. **Reply Schema**
   ```python
   {
       'reply_to': {
           'message_id': int,
           'sender_id': int,
           'sender_name': str,
           'type': str,        # message type
           'date': str,        # ISO format
           'content_preview': Optional[str]
       }
   }
   ```

3. **Forward Schema**
   ```python
   {
       'forward_origin': {
           'type': str,        # user/channel/group
           'date': str,        # ISO format
           'sender': {
               'user_id': int,
               'username': str,
               'name': str,
               'type': str     # user/bot/system
           },
           'source_chat': Optional[dict]
       }
   }
   ```

## Testing Implementation
> See [CONVENTIONS.md](.cursor/CONVENTIONS.md) for complete testing standards

### Component Tests
1. **Frame Tests**
   - Creation validation
   - Metadata integrity
   - Type handling
   - Size limit enforcement
   - Format validation
   - Hash verification

2. **Pipeline Tests**
   - Component chaining
   - Flow control
   - Error boundaries
   - Processor ordering
   - State persistence
   - Metrics collection

### Integration Tests
1. **Storage Tests**
   - Data serialization
   - File management
   - Git operations
   - Index maintenance
   - Deduplication
   - Recovery procedures

2. **Transport Tests**
   - Message handling
   - Media processing
   - State management
   - Rate limiting
   - Error recovery
   - Connection stability 