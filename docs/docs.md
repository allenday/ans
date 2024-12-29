# Chronicler

## Architecture

The system is composed of three main components:

### Scribe (currently implemented)
Real-time message recording service
- Telegram interface
- Message format conversion
- User session management
- Group monitoring configuration

### Storage (future: Codex)
Persistent storage layer
- Git-based storage adapter
- Configuration storage
- Message archival

### Archivist (planned)
Post-processing and organization system
- Implemented as GitHub Actions
- Processes archived messages
- Generates summaries and indexes
- Creates structured knowledge base

## Component Renaming Plan
- Phase 1: Rename `bot` to `scribe` (current sprint)
- Phase 2: Keep `storage` as is for now
- Phase 3: Add `archivist` as new component (future sprint)

## Current Implementation Focus
1. Scribe component (core functionality)
2. Basic storage adapters
3. User command handling
4. Message processing pipeline

See [commands.md](commands.md) for available commands and [planned GitOps features].

## Future Work
The Archivist component will provide:
- Conversation sessionization
- Summary generation
- Topic extraction
- Knowledge base organization

These features will be implemented as separate GitHub Actions that work with the chat logs stored by the scribe. 