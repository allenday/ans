# Chronicler

A Telegram bot that archives messages and media from chats into a Git repository, using a pipeline-based architecture for extensible message processing.

## Features

- Archives text messages, photos, videos, documents, stickers, and audio files
- Preserves message metadata (sender, timestamps, replies, etc.)
- Handles Telegram forum topics
- Stores media files with proper organization
- Uses Git for version control and backup
- Pipeline architecture for extensible processing

## Architecture

Chronicler uses a pipeline-based architecture with three main components:

1. **Transports**: Handle input/output with external services (e.g., Telegram)
2. **Processors**: Process messages and perform actions (e.g., storage)
3. **Pipeline**: Coordinates the flow of data between components

### Message Flow

```
[TelegramTransport] -> [StorageProcessor]
     ↓                        ↓
Receives messages     Saves to Git repo
```

### Frame Types

- `TextFrame`: For text messages
- `ImageFrame`: For photos and images
- `DocumentFrame`: For files, stickers, audio, and video

## Installation

1. Clone the repository:
```bash
git clone https://github.com/allenday/ans.git
cd ans
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Required environment variables:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `STORAGE_PATH`: Path where messages will be stored

## Usage

Run the bot:
```bash
python -m chronicler.pipeline.pipecat_runner --token YOUR_BOT_TOKEN --storage /path/to/storage
```

## Development

### Project Structure

```
src/chronicler/
├── pipeline/           # Core pipeline components
│   ├── frames.py      # Frame data structures
│   ├── pipeline.py    # Pipeline implementation
│   └── pipecat_runner.py  # Main entry point
├── processors/         # Message processors
│   └── storage_processor.py  # Git storage processor
├── storage/           # Storage implementation
│   ├── coordinator.py # Storage coordination
│   ├── filesystem.py  # File operations
│   └── telegram.py    # Telegram-specific storage
└── transports/        # Input/output handlers
    └── telegram_transport.py  # Telegram bot interface
```

### Testing

Tests are organized into three categories:
- `00-unit/`: Unit tests with mocked dependencies
- `01-mock/`: Integration tests with mocked external services
- `02-live/`: Integration tests with real external services

Run tests:
```bash
pytest tests/00-unit  # Run unit tests
pytest tests/01-mock  # Run mock integration tests
pytest tests/02-live  # Run live integration tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[Insert License Information]
