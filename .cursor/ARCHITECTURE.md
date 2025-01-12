# Chronicler Architecture

## Overview

Chronicler uses a pipeline-based architecture to process messages from Telegram and store them in a Git repository. This document covers the technical architecture. For development workflows and conventions, see [CONVENTIONS.md](.cursor/CONVENTIONS.md).

## Core Components

### 1. Pipeline

The pipeline is the central component that coordinates message flow:

```
[Transport] -> [Processor1] -> [Processor2] -> ...
```

Key classes:
- `Pipeline`: Manages the flow of frames through processors
  - Initializes with a list of processors
  - Processes frames sequentially through each processor
  - Handles errors and logging
- `BaseProcessor`: Abstract base class for all processors
  - Defines `process(frame)` interface
  - Provides logging and error handling
- `BaseTransport`: Special processor for I/O operations
  - Handles external service communication
  - Implements start/stop lifecycle

### 2. Frames

Frames are the data units that flow through the pipeline:

Base Classes:
- `Frame`: Base class for all frames
  - `text`: Main content
  - `metadata`: Dict of frame information
  - Validates types on initialization
  - Logs creation and modifications

Message Types:
- `TextFrame`: For text messages
  - Validates text content
  - Preserves formatting
- `ImageFrame`: For photos and images
  - Handles binary image data
  - Stores dimensions and format
- `DocumentFrame`: For files
  - Stores filename and mime_type
  - Handles arbitrary binary data
- `AudioFrame`: For audio files
  - Includes duration and format
- `VoiceFrame`: For voice messages
  - Similar to AudioFrame
  - Voice-specific metadata
- `StickerFrame`: For stickers
  - Stores emoji and pack info

### 3. Transports

Transports handle I/O with external services:

- `TelegramTransport`: Handles Telegram bot interactions
  - Message reception and parsing
  - Media downloading and caching
  - Metadata extraction
  - Supports all message types:
    - Text with formatting
    - Images and photos
    - Documents and files
    - Audio and voice
    - Stickers and animations
  
For transport configuration and credentials, see [CONVENTIONS.md](.cursor/CONVENTIONS.md) under Technical Style Guide.

### 4. Processors

Processors transform or store frames:

- `StorageProcessor`: Saves messages to Git
  - Message serialization to JSONL
  - File organization by type
  - Git operations (add, commit)
  - Handles concurrent writes

### 5. Storage System

Storage system for persisting messages. For branch-specific storage workflows, see [CONVENTIONS.md](.cursor/CONVENTIONS.md).

Directory Structure:
```
storage_root/
├── topics/
│   └── topic_name/
│       ├── messages.jsonl
│       └── media/
│           ├── images/
│           ├── documents/
│           └── audio/
└── .git/
```

Message Format (JSONL):
```json
{
  "content": "Message text or binary path",
  "timestamp": "2024-01-12T00:00:00Z",
  "metadata": {
    "sender": "username",
    "chat_id": 123456,
    "message_id": 789
  },
  "attachments": [
    {
      "type": "image",
      "path": "media/images/file.jpg",
      "mime_type": "image/jpeg"
    }
  ]
}
```

## Message Flow

1. **Reception**
   ```
   Telegram -> TelegramTransport -> Frame creation
   ```
   - Bot receives update from Telegram
   - Transport creates appropriate frame type
   - Metadata extracted and validated

2. **Processing**
   ```
   Frame -> StorageProcessor -> Message/File storage
   ```
   - Frame passed through pipeline
   - Media downloaded if needed
   - Message formatted for storage

3. **Storage**
   ```
   Message -> JSONL serialization -> Git commit
   ```
   - Message converted to JSONL
   - Media files saved to appropriate directory
   - Changes committed to Git

## Testing Strategy

1. **Unit Tests**
   - Frame creation and validation
   - Pipeline processing logic
   - Storage serialization
   - Individual processor behavior

2. **Mock Tests**
   - Transport with mock Telegram API
   - Storage with mock Git operations
   - Pipeline with mock processors

3. **Live Tests**
   - Full integration with Telegram
   - Complete message flow
   - Storage verification

## Design Principles

1. **Separation of Concerns**
   - Each component has a single responsibility
   - Clear interfaces between components
   - Minimal dependencies

2. **Extensibility**
   - Easy to add new processors
   - Support for different transports
   - Flexible frame types

3. **Testability**
   - Components can be tested in isolation
   - Mock interfaces for external services
   - Clear component boundaries

4. **Error Handling**
   - Graceful failure handling
   - Error logging and reporting
   - Data consistency preservation 

## Related Documentation

- [CONVENTIONS.md](.cursor/CONVENTIONS.md) - Development workflow and standards
- [IMPLEMENTATION.md](.cursor/IMPLEMENTATION.md) - Technical implementation details
- [BACKLOG.md](.cursor/BACKLOG.md) - Development roadmap and known issues