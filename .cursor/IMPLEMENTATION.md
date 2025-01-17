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

## Status Update Automation

### Overview
The status update automation system ensures consistent tracking and versioning of item completion status in PRD.md and CHECKLIST.md files.

### Components

1. **Status Update Script**
   ```
   .cursor/scripts/status-update.sh
   Usage: status-update.sh <file> <item> <old_status> <new_status> <description>
   ```
   1. Purpose:
      1. Automate git operations for status changes
      2. Ensure consistent commit messages
      3. Maintain atomic commits per status change
   2. Features:
      1. Validates status transitions (🕔 -> ✅ or ✅ -> 🕔)
      2. Generates standardized commit messages
      3. Handles git staging and commits

2. **Commit Template**
   ```
   .cursor/COMMIT.template
   Format:
   Status Update: {emoji} {action}: {item_description}
   File: {relative_path}
   Item: {section}.{subsection}
   ```
   1. Purpose:
      1. Define standard format for status updates
      2. Ensure consistent tracking
      3. Enable automated processing

3. **Commit Message Hook**
   ```
   .cursor/hooks/commit-msg
   Validates:
   1. Message format
   2. File path (.cursor/*)
   3. Item reference format
   ```
   1. Purpose:
      1. Enforce commit message standards
      2. Validate status update metadata
      3. Prevent malformed commits

### Usage

1. **Manual Status Updates**
   ```bash
   # Example: Completing an item
   .cursor/scripts/status-update.sh \
     .cursor/docs/feature/your-feature/PRD.md \
     "4.3.2" "🕔" "✅" "Add logging to core components"
   ```

2. **Validation Rules**
   1. Status changes:
      1. 🕔 -> ✅: Marking item as complete
      2. ✅ -> 🕔: Reopening item
   2. File paths:
      1. Must be under .cursor/
      2. Must exist in repository
   3. Item references:
      1. Must use dot notation (e.g., 4.3.2)
      2. Must exist in referenced file

3. **Error Handling**
   1. Invalid status transitions
   2. Malformed commit messages
   3. Missing or invalid files
   4. Invalid item references

### Integration

1. **Installation**
   ```bash
   # Set up commit template
   git config --local commit.template .cursor/COMMIT.template

   # Install commit hook
   mkdir -p .git/hooks
   ln -sf ../../.cursor/hooks/commit-msg .git/hooks/commit-msg
   ```

2. **Maintenance**
   1. Keep scripts executable:
      ```bash
      chmod +x .cursor/scripts/status-update.sh
      chmod +x .cursor/hooks/commit-msg
      ```
   2. Update templates as needed
   3. Monitor hook performance 

## Process Control Specifications

### 1. State Management
🔒 STATE TRACKING PROTOCOL
1. Pre-Operation State
   ```
   🔒 PRE-OP CAPTURE
   - Branch state
   - Documentation state
   - Tool chain state
   - Validation status
   ```

2. Mutation Tracking
   ```
   🔒 MUTATION LOG
   - Operation ID
   - Tool chain sequence
   - File mutations
   - State transitions
   ```

3. Atomic Operations
   ```
   🔒 ATOMIC GUARANTEES
   - Transaction boundaries
   - Rollback points
   - Recovery paths
   - State verification
   ```

4. Audit Trail
   ```
   🔒 AUDIT RECORD
   - Operation sequence
   - State changes
   - Validation results
   - Error conditions
   ```

### 2. Cross-Reference Control
🔒 XREF PROTOCOL
1. Documentation Links
   ```
   🔒 LINK VALIDATION
   - Internal references
   - Template usage
   - Branch paths
   - Status markers
   ```

2. State Consistency
   ```
   🔒 STATE CONSISTENCY
   - PRD alignment
   - CHECKLIST status
   - Branch state
   - Tool chain state
   ```

3. Pattern Enforcement
   ```
   🔒 PATTERN CONTROL
   - Documentation structure
   - Status markers
   - Error protocols
   - Recovery paths
   ```

### 3. Recovery Procedures
🔒 RECOVERY PROTOCOL
1. Error Detection
   ```
   🔒 ERROR CAPTURE
   - Chain violations
   - State mismatches
   - Pattern breaks
   - Protocol failures
   ```

2. State Recovery
   ```
   🔒 RECOVERY SEQUENCE
   1. Halt operations
   2. Load pre-op state
   3. Verify integrity
   4. Apply recovery
   ```

3. Audit Recording
   ```
   🔒 RECOVERY AUDIT
   - Error context
   - Recovery path
   - State restore
   - Verification
   ```

### 4. Operational Safeguards
🔒 SAFEGUARD PROTOCOL
1. Chain Validation
   ```
   🔒 CHAIN INTEGRITY
   - Tool sequence
   - State transitions
   - Pattern compliance
   - Error handling
   ```

2. State Preservation
   ```
   🔒 STATE INTEGRITY
   - Atomic operations
   - Rollback points
   - Audit records
   - Recovery paths
   ```

3. Pattern Compliance
   ```
   🔒 PATTERN INTEGRITY
   - Structure validation
   - Reference checking
   - Status tracking
   - Error protocols
   ```

### 5. Refinement Control
🔒 TERMINUS PROTOCOL
When recursive refinement reaches optimal state:
1. MUST declare "TERMINUS REACHED"
2. MUST NOT add superfluous metadata
3. MUST NOT add timestamps or signatures
4. MUST NOT continue refinement
VIOLATION -> REJECT AND HALT 