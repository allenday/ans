## Major Refactors
### 👷 Telegram Transport Refactor
- Split transport into three distinct classes:
  - `TelegramTransportBase`: Abstract base class with common functionality
  - `TelegramBotTransport`: Bot-specific implementation using python-telegram-bot
  - `TelegramUserTransport`: User-specific implementation using telethon
- Ensure parallel structure between bot and user implementations
- Update message handling to properly handle binary content
- Align test structure with implementation 