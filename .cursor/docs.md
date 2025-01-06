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
    <group_id>/           # Numerical Telegram chat_id
      <topic_id>/         # Numerical Telegram topic_id
        messages.jsonl    # Message content and metadata
        attachments/      # Media attachments directory
          jpg/           # Photo attachments
          mp4/           # Video attachments
          webp/          # Sticker attachments
          pdf/           # Document attachments
          ogg/           # Voice message attachments
          mp3/           # Audio attachments
  metadata.yaml          # Repository-wide metadata and name mappings
```

## Key Points

1. Directory Structure
   - All content is under the `telegram` directory
   - Groups are identified by Telegram chat_id (numerical)
   - Topics are identified by Telegram topic_id (numerical)
   - Media files are stored in type-specific subdirectories

2. File Organization
   - `messages.jsonl`: Contains message content and metadata in JSONL format
   - `attachments/`: Directory for all media files
   - Media subdirectories are created based on file types (jpg, mp4, etc.)

3. Attachment Handling
   - Files are saved using Telegram's unique file_id: `<file_id>.<extension>`
   - Original filenames are preserved in message metadata
   - Supported media types:
     * Photos: `.jpg` in `jpg/`
     * Videos: `.mp4` in `mp4/`
     * Stickers: `.webp` in `webp/`
     * Documents: preserved extension in matching directory
     * Voice messages: `.ogg` in `ogg/`
     * Audio files: `.mp3` in `mp3/`

4. Metadata and Mappings
   - Repository-wide settings and mappings in `metadata.yaml`:
     ```yaml
     telegram:
       groups:
         "123456789":           # group_id
           name: "Group Name"   # human-readable name
           topics:
             "987654321":       # topic_id
               name: "Topic Name" # human-readable name
     ```
   - Per-message metadata in `messages.jsonl` includes:
     ```json
     {
       "content": "message text",
       "attachments": [
         {
           "file_id": "ABC123",
           "original_name": "photo.jpg",
           "mime_type": "image/jpeg"
         }
       ]
     }
     ```

## Path Construction

When constructing paths:
1. Topic directory: `telegram/<group_id>/<topic_id>/`
2. Messages file: `telegram/<group_id>/<topic_id>/messages.jsonl`
3. Attachments: `telegram/<group_id>/<topic_id>/attachments/<media_type>/<file_id>.<extension>`

## Implementation Notes

1. Directory Creation
   - Directories are created using numerical IDs
   - Human-readable names stored only in metadata.yaml
   - All paths are sanitized to be filesystem-safe

2. File Handling
   - Messages are appended to JSONL files
   - Attachments are saved using Telegram's unique file_ids
   - Original filenames preserved in message metadata
   - File permissions preserve read/write access

3. Git Integration
   - All changes are tracked in Git
   - Commits are atomic per message/attachment
   - Remote synchronization via GitHub

4. Name Resolution
   - Group and topic names are resolved through metadata.yaml
   - UI/Bot can present human-readable names while using IDs internally
   - Names can be updated without affecting the directory structure 