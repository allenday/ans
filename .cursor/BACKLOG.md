# Development Backlog

## Current Sprint

### In Progress
- [ ] Clean up old implementation files
- [ ] Reorganize test structure
- [ ] Update documentation

### Next Up
- [ ] Add support for video notes
- [ ] Add support for polls
- [ ] Add support for location messages

## Future Work

### Features
- [ ] Add support for message editing
- [ ] Add support for message deletion
- [ ] Add support for pinned messages
- [ ] Add support for channel posts
- [ ] Add support for inline keyboards
- [ ] Add support for message reactions
- [ ] Add support for message threads (supergroups)
- [ ] Add support for message search
- [ ] Add Twitter Transport for bookmark archival
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

### Improvements
- [ ] Optimize media file storage
- [ ] Add compression for large files
- [ ] Improve error recovery
- [ ] Add rate limiting
- [ ] Add message batching
- [ ] Add periodic storage cleanup
- [ ] Add storage statistics

### Technical Debt
- [ ] Add comprehensive logging
- [ ] Add performance metrics
- [ ] Add monitoring hooks
- [ ] Improve test coverage
- [ ] Add integration tests for all message types
- [ ] Add load tests
- [ ] Add benchmarks

### Documentation
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