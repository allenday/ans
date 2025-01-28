# 1. Message Sender Refactoring PRD

## 1.1 Overview
Extract and centralize message sending logic from Telegram transport implementations into a dedicated `TelegramMessageSender` class to improve code organization, reduce duplication, and simplify maintenance.

## 1.2 Goals
1. Extract message sending logic into a dedicated class
2. Reduce code duplication between bot and user transports
3. Maintain existing test coverage and behavior
4. Improve code maintainability and testability

## 1.3 Current State
1. Message sending logic is duplicated between `TelegramBotTransport` and `TelegramUserTransport`
2. Both transports handle message sending similarly but with slight API differences
3. Testing focuses on end results rather than implementation details

## 1.4 Requirements

### 1.4.1 Functional Requirements
1. Support sending text messages with:
   a. Chat ID
   b. Message content
   c. Optional thread ID/reply ID
2. Support sending images with:
   a. Chat ID
   b. Image content
   c. Optional caption
   d. Optional thread ID/reply ID
3. Handle both bot (python-telegram-bot) and user (telethon) client APIs
4. Maintain existing metadata handling and frame updates

### 1.4.2 Non-Functional Requirements
1. No changes to external transport behavior
2. Maintain or improve test coverage
3. Clear separation of concerns
4. Consistent error handling
5. Proper logging and tracing

## 1.5 Design

### 1.5.1 TelegramMessageSender
1. Single class responsible for message sending
2. Handles both bot and user client APIs
3. Provides unified interface for sending different frame types
4. Maintains consistent error handling and logging

### 1.5.2 Transport Changes
1. Remove message sending logic from transports
2. Initialize sender during authentication/start
3. Delegate send operations to sender instance

### 1.5.3 Testing Strategy
1. Maintain existing transport tests
2. Add dedicated sender unit tests
3. Test both bot and user API scenarios
4. Verify error handling and edge cases

## 1.6 Implementation Plan
1. Create `TelegramMessageSender` class
2. Implement core sending methods
3. Update transport classes to use sender
4. Add sender-specific tests
5. Verify existing tests pass
6. Update documentation

## 1.7 Success Metrics
1. No changes to external behavior
2. Reduced code duplication
3. Improved test coverage
4. Cleaner code organization
5. Simplified maintenance path

## 1.8 Refactored structure

Would look like this, we make minimum changes toward it to minimize impact of renaming as we work.

src/chronicler/transports/
├── __init__.py
├── abstract
│   ├── __init__.py
│   ├── sender.py (new file)
│   └── transport.py
├── events
│   ├── __init__.py
│   ├── base.py
│   └── telegram
│       ├── __init__.py
│       ├── bot.py
│       ├── bot_update.py
│       ├── update.py
│       ├── update_user.py
│       ├── user.py
│       └── user_update.py
└── telegram
    ├── __init__.py
    ├── factory.py
    ├── message_sender.py
    ├── sender
    │   ├── __init__.py
    │   ├── base.py (new file)
    │   ├── bot.py
    │   └── user.py (was telegram/transport/user.py)
    └── transport
        ├── __init__.py
        ├── base.py
        ├── bot.py (done)
        └── user.py