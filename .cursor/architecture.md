# Chronicler Architecture

## Overview

Chronicler uses a pipeline-based architecture to process messages from Telegram and store them in a Git repository. The architecture is designed to be extensible and maintainable.

## Core Components

### 1. Pipeline

The pipeline is the central component that coordinates message flow:

```
[Transport] -> [Processor1] -> [Processor2] -> ...
```

Key classes:
- `Pipeline`: Manages the flow of frames through processors
- `BaseProcessor`: Abstract base class for all processors
- `BaseTransport`: Special processor for I/O operations

### 2. Frames

Frames are the data units that flow through the pipeline:

- `Frame`: Base class for all frames
- `TextFrame`: For text messages
- `ImageFrame`: For photos and images
- `DocumentFrame`: For files, audio, video, stickers

Each frame includes:
- Content (text, binary data, etc.)
- Metadata (sender, timestamps, etc.)
- Type-specific attributes

### 3. Transports

Transports handle I/O with external services:

- `TelegramTransport`: Handles Telegram bot interactions
  - Message reception
  - Media downloading
  - Metadata extraction

### 4. Processors

Processors transform or store frames:

- `StorageProcessor`: Saves messages to Git
  - Message serialization
  - File organization
  - Git operations

### 5. Storage

Storage system for persisting messages:

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

## Message Flow

1. **Reception**
   ```
   Telegram -> TelegramTransport -> Frame creation
   ```

2. **Processing**
   ```
   Frame -> StorageProcessor -> Message/File storage
   ```

3. **Storage**
   ```
   Message -> JSONL serialization -> Git commit
   ```

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