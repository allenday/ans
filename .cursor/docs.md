# Project Documentation

## Current State

### Storage System (Completed)
- Git-based storage implementation ✓
- Topic and message organization ✓
- Local and remote repository support ✓
- JSONL format for messages ✓
- Attachment handling ✓
- Comprehensive test coverage ✓

### Core Components
- Message interface and data models ✓
- Storage adapter abstraction ✓
- GitHub integration for remote storage ✓

## Next Sprint: Telegram Bot Integration

### Bot Core
1. Message Handling
   - Private chat configuration
   - Group chat monitoring
   - Message to storage pipeline
   - Media attachment handling

2. Configuration Management
   - GitHub token setup
   - Repository configuration
   - User preferences
   - Per-group settings

3. State Management
   - User sessions
   - Configuration flows
   - Active conversations

### Interface Classes

```python
class BotConfig:
    """Bot configuration and settings"""
    token: str
    admin_users: List[int]
    github_token: Optional[str]
    github_repo: Optional[str]

class UserSession:
    """Track user interaction state"""
    user_id: int
    state: str
    context: Dict[str, Any]
    config: BotConfig

class GroupConfig:
    """Per-group settings"""
    group_id: int
    topic_id: str
    enabled: bool
    filters: Dict[str, Any]

class ChroniclerBot:
    """Main bot class"""
    async def start(self):
        """Start the bot"""
    
    async def handle_message(self, update: Update):
        """Process incoming messages"""
    
    async def handle_command(self, update: Update):
        """Handle bot commands"""
```

### Development Tasks
1. [ ] Set up bot framework with python-telegram-bot
2. [ ] Implement configuration management
3. [ ] Add private chat command handling
4. [ ] Add group chat monitoring
5. [ ] Integrate with storage system
6. [ ] Add user session management
7. [ ] Implement configuration flows
8. [ ] Add comprehensive tests
9. [ ] Document bot usage and commands

### Testing Strategy
1. Unit Tests
   - Command handling
   - Configuration management
   - Message processing

2. Integration Tests
   - Bot initialization
   - Storage integration
   - Configuration flows

3. Mock Tests
   - Telegram API interactions
   - GitHub integration
   - Message handling pipeline 

# Repository Structure

The repository follows this structure for storing Telegram messages and media:

```
<github root>/
  telegram/
    <group name>/           # From chat.title or "default"
      <topic name>/         # User-specified topic name
        messages.jsonl      # Message content and metadata
        attachments/        # Media attachments directory
          jpg/             # Photo attachments
          mp4/             # Video attachments
          webp/            # Sticker attachments
          pdf/             # Document attachments
          ogg/             # Voice message attachments
          mp3/             # Audio attachments
  metadata.yaml            # Repository-wide metadata
```

## Key Points

1. Directory Structure
   - All content is under the `telegram` directory
   - Group names come from chat titles (falls back to "default")
   - Topics are user-defined and organized under group directories
   - Media files are stored in type-specific subdirectories

2. File Organization
   - `messages.jsonl`: Contains message content and metadata in JSONL format
   - `attachments/`: Directory for all media files
   - Media subdirectories are created based on file types (jpg, mp4, etc.)

3. Attachment Handling
   - Files are saved with format: `<message_id>_<file_id>.<extension>`
   - Supported media types:
     * Photos: `.jpg` in `jpg/`
     * Videos: `.mp4` in `mp4/`
     * Stickers: `.webp` in `webp/`
     * Documents: preserved extension in matching directory
     * Voice messages: `.ogg` in `ogg/`
     * Audio files: `.mp3` in `mp3/`

4. Metadata
   - Repository-wide settings in `metadata.yaml`
   - Per-message metadata stored in `messages.jsonl`
   - Media metadata (duration, size, etc.) included in message entries

## Path Construction

When constructing paths:
1. Topic directory: `telegram/<group_name>/<topic_name>/`
2. Messages file: `telegram/<group_name>/<topic_name>/messages.jsonl`
3. Attachments: `telegram/<group_name>/<topic_name>/attachments/<media_type>/<message_id>_<file_id>.<extension>`

## Implementation Notes

1. Directory Creation
   - Directories are created on-demand when saving messages
   - Media type directories are created when first needed
   - All paths are sanitized to be filesystem-safe

2. File Handling
   - Messages are appended to JSONL files
   - Attachments are saved with unique IDs to prevent conflicts
   - File permissions preserve read/write access

3. Git Integration
   - All changes are tracked in Git
   - Commits are atomic per message/attachment
   - Remote synchronization via GitHub 