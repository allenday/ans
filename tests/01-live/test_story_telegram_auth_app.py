"""User story for Telegram authentication flow.

As a user,
I want to authenticate with Telegram through the bot
So that I can use the app with my Telegram account

The flow:
1. User sends /start command to bot
2. Bot asks for API ID
3. User provides API ID through Telegram chat
4. Bot asks for API hash
5. User provides API hash through Telegram chat
6. Bot asks for phone number
7. User provides phone number through Telegram chat
8. Bot requests OTP that Telegram sent
9. User provides OTP through Telegram chat
10. Bot confirms successful connection
"""

import os
import pytest
import pytest_asyncio
from pathlib import Path
import asyncio

from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.commands.processor import CommandProcessor
from chronicler.handlers.command import StartCommandHandler
from chronicler.pipeline.pipeline import Pipeline

@pytest.fixture
def test_config():
    """Load test configuration from environment."""
    required_vars = [
        'TELEGRAM_CHRONICLER_BOT_TOKEN'
    ]
    
    config = {}
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            pytest.skip(f'Required environment variable {var} not set')
        config[var] = value
        
    return config

@pytest_asyncio.fixture
async def bot_transport(test_config):
    """Initialize bot transport."""
    transport = TelegramBotTransport(test_config['TELEGRAM_CHRONICLER_BOT_TOKEN'])
    await transport.authenticate()
    await transport.start()
    await asyncio.sleep(1)  # Give the transport a moment to fully initialize
    yield transport
    # Don't stop the transport - let it keep running for user interaction

@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test storage."""
    return tmp_path

@pytest.fixture
def storage_coordinator(temp_dir):
    """Initialize storage processor."""
    return StorageProcessor(temp_dir)

@pytest.fixture
def command_processor(storage_coordinator):
    """Initialize command processor with handlers."""
    processor = CommandProcessor()
    # Don't register the handler here since we'll register it with the transport
    return processor

@pytest.mark.asyncio
async def test_telegram_auth_flow(test_config, bot_transport,
                                storage_coordinator, command_processor):
    """Test the Telegram authentication flow with live user interaction."""

    # Create pipeline
    pipeline = Pipeline()
    pipeline.add_processor(command_processor)
    pipeline.add_processor(bot_transport)
    pipeline.add_processor(storage_coordinator)

    # Register the start command handler with the transport
    start_handler = StartCommandHandler(storage_coordinator)
    print("\nRegistering /start command handler...")
    await bot_transport.register_command("start", start_handler.handle)
    print("Command handler registered")

    print("\nBot is ready for interaction!")
    print("Please send /start to the bot in Telegram")
    print("Press Ctrl+C when you want to stop the bot")
    
    try:
        # Keep processing messages until user interrupts
        while True:
            print(".", end="", flush=True)  # Show activity
            # Process any incoming messages through the pipeline
            frame = await bot_transport.receive()
            if frame:
                print(f"\nReceived frame: {frame.__class__.__name__}")
                if hasattr(frame, 'command'):
                    print(f"Command: {frame.command}")
                if hasattr(frame, 'content'):
                    print(f"Content: {frame.content}")
                if hasattr(frame, 'metadata'):
                    print(f"Metadata: {frame.metadata}")
                
                # Process frame through pipeline and send any response
                print("Processing frame through pipeline...")
                response = await pipeline.process(frame)
                if response:
                    print(f"Got response: {response.__class__.__name__}")
                    if hasattr(response, 'content'):
                        print(f"Response content: {response.content}")
                    print("Sending response...")
                    await bot_transport.send(response)
                    print("Response sent")
                else:
                    print("No response from pipeline")
            await asyncio.sleep(0.1)  # Small delay to prevent busy loop
    except KeyboardInterrupt:
        print("\nStopping bot...")
        await bot_transport.stop()
        print("Bot stopped.") 