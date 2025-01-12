# Development Backlog    

### Future Work  

1. Add per-user multi-tenancy  
   - Requirements:  
     - Per-user chat configuration  
     - Independent git repository credentials for each user  
   - Components:  
     - UserConfigurationManager  
     - CommandHandler updates  
   - Constraints:  
     - Secure credential handling  
     - Configuration persistence  
     - Clear feedback for user errors  

2. Add Twitter Transport for bookmark archival  
   - Requirements:  
     - Authenticate with Twitter API  
     - Poll for new bookmarks periodically  
     - Download tweet content and media  
     - Store in Git with metadata  
     - Remove bookmark after successful storage  
   - Components:  
     - TwitterTransport class  
     - Tweet to DocumentFrame conversion  
     - Media attachment handling  
     - Bookmark management  
   - Constraints:  
     - Must handle Twitter API rate limits  
     - Must verify successful storage before unbookmarking  
     - Must handle network failures gracefully  
     - Must preserve all tweet metadata  
   - Storage Format:  
     - tweets/  
       - YYYY-MM-DD/  
         - tweet_id.json (metadata)  
         - media/ (attachments)  
    
3. Log rotation and summarization  
  
   - Requirements:  
     - Daily rotation of messages.jsonl  
     - Archive old logs by date  
     - Maintain consistent git history  
     - Generate daily summaries  
   - Components:  
     - Log rotation workflow  
     - Message sessionization script  
     - Summary generation  
     - Archive management  
   - Schedule:  
     - Run daily at midnight UTC  
     - Process previous day's messages  
     - Generate daily statistics  
   - Outputs:  
     - archives/YYYY-MM-DD/messages.jsonl  
     - summaries/YYYY-MM-DD/  
       - sessions.json (conversation threads)  
       - statistics.json (message counts, types)  
       - topics.json (extracted topics)  
       - participants.json (active users)  

4. Advanced message handling  
- [ ] Add support for topic branching (by forwarding a message)  
- [ ] Add support for message editing  
- [ ] Add support for message deletion  
- [ ] Add support for pinned messages  
- [ ] Add support for channel posts  
- [ ] Add support for inline keyboards  
- [ ] Add support for message reactions  
- [ ] Add support for message threads (supergroups)  
- [ ] Add support for message search  

5. Async post processing as github actions  
- [ ] Add link expansion and archival  
   - Requirements:  
     - Detect URLs in messages  
     - Download webpage content as PDF  
     - Save complete webpage with assets  
     - Store in Git with metadata  
     - Handle various content types appropriately  
   - Components:  
     - LinkDetector class  
     - WebpageArchiver class  
     - Content type handlers  
     - Download management  
   - Constraints:  
     - Must handle large webpages gracefully  
     - Must preserve webpage styling and assets  
     - Must handle network failures  
     - Must respect robots.txt and rate limits  
   - Storage Format:  
     - links/  
       - YYYY-MM-DD/  
         - domain/  
           - webpage_id/  
             - metadata.json  
             - content.pdf  
             - complete/  
  

  
## Tech Debt Status

- ✅ Comprehensive operation logging
- 🕔 Comprehensive unit tests
- 🕔 Comprehensive mock tests
- 🕔 Comprehensive live tests
- 🕔 Docstrings on all classes and methods
- 🕔 PydanticAI on all classes and methods
- 🕔 Error handling on all classes and methods
- 🕔 Performance metrics
- 🕔 Monitoring hooks  
- 🕔 Add proper error recovery mechanisms

## Documentation Status

- 🕐 Comprehensive user documentation  
- 🕐 Comprehensive developer documentation  
- 🕐 Add deployment guide  
- 🕐 Add troubleshooting guide  
- 🕐 Add configuration guide  

## Implementation Status

### Comamands

- ✅ Basic command processing infrastructure
- ✅ Core command handlers:
  - ✅ `/start`
  - ✅ `/config`
  - ✅ `/status`
  - 🕐 `/help`

### Frames

- ✅ Base frame infrastructure
- ✅ TextFrame implemented for text messages
- ✅ CommandFrame implemented for command messages
- ✅ MediaFrame base class implemented for media messages
  - 🏗️ Photos: in progress in ImageFrame
  - 🏗️ Audio files: in progress in AudioFrame
  - 🏗️ Documents: in progress in DocumentFrame
  - 🏗️ Voice messages: in progress in VoiceFrame
  - 🏗️ Stickers: in progress in StickerFrame
  - 🕔 Video messages: in progress in VideoFrame
  - 🕔 Video files
  - 🕔 Locations
  - 🕔 Contacts
  - 🕔 Polls
  - 🕔 Invoices

### Handlers

- ✅ Base handler infrastructure
- 🏗️  `/start` in progress in StartCommandHandler
- 🏗️  `/config` in progressin ConfigCommandHandler
- 🏗️  `/status` in progress in StatusCommandHandler

### Pipeline

- ✅ Core pipeline infrastructure
- ✅ Basic runner implementation
- 🕐 Pipeline features needed:
  - 🕐 Error recovery
  - 🕐 Monitoring
  - 🕐 Configuration
  - 🕐 State persistence
  - 🕐 Health checks
  - 🕐 Metrics

### Services

- ✅ Git sync service
- 🕐 Media processing service
- 🕐 Health monitoring service
- 🕐 Metrics service

### Storage

- ✅ Core storage infrastructure
- ✅ Git-based storage implementations
  - ✅ synchronous git commit on outgoing and incoming messages
  - ✅ environment-based git configuration
  - ✅ basic file organization
  - 🕐 Periodic async synchronization with upstream (pull/push)
    - 🕔 basic retry mechanism for push failures
  - 🕐 Conflict resolution
  - 🕐 Log rotation

### Transport

- ✅ Core transport infrastructure
- ✅ Telegram transport implementations
  - ✅ support Telethon for telegram transport
  - ✅ support python-telegram-bot for telegram transport
- ✅ Message type support
  - ✅ In-sync with Frame Media types
- 🕔 Twitter transport
- 🕔 Discord transport
- 🕔 Slack transport
- 🕔 Move MessageReceiver from tests to library for easier message verification

## GitOps Status

- 🕔 CI/CD automation on merge to main
  - 🕔 Secrets storage and management
  - 🕔 Run all unit tests
  - 🕔 Run all mock tests

