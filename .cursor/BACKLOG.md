# Development Backlog  
  
## Current Sprint  
  
### In Progress  
- None  
  
### Next Up  
1. Implement core slash commands  
   - Priority commands:  
     - /start - Initialize bot configuration  
     - /config - Set git repository URL and credentials  
     - /status - Show current settings and state  
   - Requirements:  
     - Command handler framework  
     - Configuration persistence  
     - Secure credential management  
     - Clear user feedback  
   - Testing needs:  
     - Unit tests for command parsing  
     - Mock tests for configuration storage  
     - Live tests for git integration  
  
2. Complete test coverage for existing features  
   - Message types to test:  
     - Text messages with replies  
     - Images with captions  
     - Documents with metadata  
     - Audio files  
     - Voice messages  
     - Stickers  
   - Test levels needed:  
     - Unit: Frame creation and validation  
     - Mock: Storage operations  
     - Live: End-to-end message flow  
   - Test infrastructure:  
     - TestBot implementation  
     - Mock storage backend  
     - Test data fixtures  
  
3. Implement TestBot for command validation  
   - Test scenarios:  
     - Command sequence validation  
     - Error handling  
     - Configuration persistence  
     - Multi-user interactions  
   - Implementation:  
     - Command simulation  
     - Response validation  
     - State verification  
  
4. Implement asynchronous git operations  
   - Requirements:  
     - Commit messages on a cron schedule  
     - Decouple message receipt from git pushes  
     - Provide operation status  
   - Components:  
     - Cron-based GitOperationQueue  
     - StatusReporter  
   - Constraints:  
     - Memory-efficient queuing  
     - Performance optimization  
     - Basic retry mechanism for failures  
  
5. Add per-user multi-tenancy  
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
  
6. Add Twitter Transport for bookmark archival  
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
  
## Future Work  
  
### Features  
- [ ] Add multi-tenant support for group chats  
  - Requirements:  
    - Bot configuration via slash commands  
    - Per-group chat configuration  
    - Multiple git repository support  
    - User authorization management  
  - Commands:  
    - /start - Initialize bot in group  
    - /config - Configure git repository  
    - /status - Show current settings  
  - Components:  
    - MultiTenantCoordinator  
  - Constraints:  
    - Secure credential handling  
    - Clear access controls  
    - Configuration persistence  
  
- [ ] Add log rotation and summarization  
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
  
- [ ] Add support for topic branching (by forwarding a message)  
- [ ] Add support for message editing  
- [ ] Add support for message deletion  
- [ ] Add support for pinned messages  
- [ ] Add support for channel posts  
- [ ] Add support for inline keyboards  
- [ ] Add support for message reactions  
- [ ] Add support for message threads (supergroups)  
- [ ] Add support for message search  
  
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
  
### Improvements  
- [ ] Optimize media file storage  
- [ ] Add compression for large files  
- [ ] Improve error recovery  
- [ ] Add rate limiting  
- [ ] Add message batching  
- [ ] Add periodic storage cleanup  
- [ ] Add storage statistics  
  
### Technical Debt  
- [ ] Clean up old implementation files  
- [ ] Reorganize test structure  
- [ ] Add comprehensive logging  
- [ ] Add performance metrics  
- [ ] Add monitoring hooks  
- [ ] Complete test coverage matrix  
  - Requirements:  
    - All message types covered in unit tests  
    - All error conditions covered in mock tests  
    - All external integrations covered in live tests  
  - Test Structure:  
    - Unit: Core logic and data structures  
    - Mock: External service interactions  
    - Live: End-to-end workflows  
  - Coverage Goals:  
    - Unit tests: 100% coverage  
    - Mock tests: All error conditions  
    - Live tests: All supported message types  
- [ ] Implement pydanticAI throughout codebase  
  - Requirements:  
    - Convert all data models to pydanticAI  
    - Add type validation everywhere  
    - Implement serialization/deserialization  
  - Components:  
    - Message models  
    - Frame models  
    - Configuration models  
    - Transport models  
  - Benefits:  
    - Runtime type safety  
    - Automatic validation  
    - Better IDE support  
    - Cleaner serialization  
- [ ] Expand documentation  
  - Code Documentation:  
    - Docstrings for all classes  
    - Type hints everywhere  
    - Usage examples  
    - Architecture diagrams  
  - User Documentation:  
    - Setup guides  
    - Configuration reference  
    - Message type support  
    - Storage format specs  
  - Developer Documentation:  
    - Contributing guidelines  
    - Test writing guide  
    - Architecture decisions  
    - Data flow diagrams  
  
### Documentation  
- [ ] Update documentation  
- [ ] Add API documentation  
- [ ] Add deployment guide  
- [ ] Add troubleshooting guide  
- [ ] Add message format specification  
- [ ] Add storage format specification  
- [ ] Add configuration guide  
  
## Known Issues  
- [ ] Voice messages saved with incorrect extension  
- [ ] Large files cause memory pressure  
- [ ] Missing error handling for network issues  
- [ ] Missing retry logic for failed operations  
  
## Completed  
- [x] Basic pipeline architecture  
- [x] Text message support  
- [x] Image message support  
- [x] Document message support  
- [x] Audio message support  
- [x] Voice message support  
- [x] Sticker message support  
- [x] Reply metadata support  
- [x] Forward metadata support  
- [x] Topic support  
- [x] Basic test structure