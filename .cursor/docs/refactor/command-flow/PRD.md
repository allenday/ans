# Command Flow Refactor PRD

## Overview
This refactor aims to simplify and streamline how commands are handled in the Chronicler bot, focusing specifically on the command registration and execution flow. The goal is to reduce complexity and eliminate overlapping responsibilities while maintaining existing interfaces.

## Current Pain Points
1. Duplicate command registration between Transport and CommandProcessor
2. Unclear responsibility for command handling between components
3. Complex message flow making debugging difficult
4. Mixed concerns in command response handling

## Proposed Changes

### 1. Command Registration ✅
1. Move all command registration to CommandProcessor ✅
2. Remove command registration from TelegramBotTransport ✅
3. Simplify command handler interface ✅

```python
# Before
await bot_transport.register_command("start", handler.handle)
processor.register_handler(StartCommandHandler(storage), "/start")

# After
processor.register_command("start", handler.handle)
```

### 2. Command Flow ✅
Before:
```
User -> Transport -> Queue -> Pipeline -> CommandProcessor -> Handler -> Queue -> Transport
```

After:
```
User -> Transport -> Pipeline -> CommandProcessor -> Handler -> Transport
```

### 3. Response Handling ✅
   1. Simplify response path ✅
   2. Remove queueing for command responses ✅
   3. Direct transport send for responses ✅

### 4. Interface Changes ✅
1. No changes to Frame interfaces ✅
2. No changes to Pipeline interface ✅
3. Minor changes to Transport interface (remove command methods) ✅
4. Minor changes to CommandProcessor interface (simplified registration) ✅

## 5. Non-Goals
1. No changes to storage layer
2. No changes to frame types
3. No changes to pipeline architecture
4. No changes to handler business logic

## 6. Success Metrics ✅
1. Reduced code complexity ✅
2. Simpler debugging flow ✅
3. All existing tests pass ✅
4. Command handling works reliably ✅

## 7. Implementation Phases
1. Remove command registration from Transport ✅
2. Update CommandProcessor interface ✅
3. Handle stateful commands ✅
4. Simplify response handling ✅
5. Update tests ✅
6. Verify functionality ✅

## 8. Migration ✅
1. No migration needed for users ✅
2. Minor updates needed for test code ✅

## 9. Testing
1. All existing tests should continue to pass
2. Focus on command handling integration tests
3. Verify command flow with live bot testing 