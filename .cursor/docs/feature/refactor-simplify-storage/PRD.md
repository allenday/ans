# Storage System Simplification

## Overview
The current storage system uses three separate backends (Git, Filesystem, and Telegram) which adds unnecessary complexity. This refactoring will simplify the storage system to use only Git storage, eliminating the need for separate filesystem storage and unused Telegram storage.

## Motivation
1. Current system has redundant storage backends
2. Maintaining consistency between Git and filesystem storage is complex
3. Error handling and rollback logic is complicated
4. Telegram storage is unused but still initialized
5. Code is more complex than necessary

## Goals
1. Simplify storage architecture to use only Git storage
2. Maintain all current functionality
3. Improve atomicity of storage operations
4. Reduce code complexity
5. Eliminate potential consistency issues

## Non-Goals
1. Change the storage interface
2. Modify how messages/attachments are serialized
3. Change Git storage implementation details
4. Modify the public API

## Technical Design

### Storage Coordinator Changes
1. Remove FileSystemStorage and TelegramStorage dependencies
2. Modify StorageCoordinator to use only GitStorageAdapter
3. Simplify attachment handling to store everything in Git
4. Update error handling and retry logic
5. Remove filesystem-specific code paths

### Git Storage Changes
1. Update GitStorageAdapter to handle attachments directly
2. Ensure proper file organization within Git repository
3. Maintain efficient storage of binary files

### Migration Plan
1. No migration needed - existing data structure in Git is sufficient
2. New messages will be stored entirely in Git
3. Old messages with filesystem attachments will still be accessible

## Testing Plan
1. Update unit tests to remove filesystem storage expectations
2. Add tests for direct attachment storage in Git
3. Test large file handling
4. Verify message retrieval with attachments
5. Test error conditions and recovery

## Success Metrics
1. Reduced code complexity (fewer lines, simpler logic)
2. All tests passing
3. No regressions in functionality
4. Improved atomicity of storage operations

## Timeline
1. Remove unused storage backends - 1 hour
2. Update StorageCoordinator - 2 hours
3. Update tests - 1 hour
4. Code review and fixes - 1 hour

Total: ~5 hours

## Risks
1. **Low Risk**: Large file handling in Git
   - Mitigation: Git handles binary files efficiently
   - Telegram limits file sizes anyway
2. **Low Risk**: Migration of existing data
   - Mitigation: No migration needed, structure remains compatible 