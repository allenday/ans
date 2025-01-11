"""Live tests for Telegram command interactions."""
import os
import pytest
import logging
import asyncio
import pytest_asyncio
from typing import AsyncGenerator

from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.transports.telegram_factory import (
    TelegramTransportFactory,
    TelegramUserTransport,
    TelegramBotTransport
)
from chronicler.transports.events import EventMetadata

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Set up logging for all tests."""
    caplog.set_level(logging.DEBUG)
    yield

@pytest_asyncio.fixture
async def user_transport():
    """Create a real user transport."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        api_id=os.environ["TELEGRAM_API_ID"],
        api_hash=os.environ["TELEGRAM_API_HASH"],
        phone_number=os.environ["TELEGRAM_PHONE_NUMBER"]
    )
    await transport.start()
    yield transport
    await transport.stop()

@pytest_asyncio.fixture
async def bot_transport():
    """Create a real bot transport."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"]
    )
    await transport.start()
    yield transport
    await transport.stop()

@pytest.mark.asyncio
async def test_user_sends_command_to_bot(user_transport: TelegramUserTransport, bot_transport: TelegramBotTransport, caplog):
    """Test sending commands from user to bot."""
    # Get bot chat ID - we need to start a chat first
    bot_info = await bot_transport.app.bot.get_me()
    bot_username = bot_info.username
    
    # Send initial message to create chat
    init_frame = TextFrame(
        text="Hello bot!",
        metadata=EventMetadata(
            chat_id=f"@{bot_username}",
            chat_title=None,
            sender_id=None,
            sender_name=None,
            message_id=0
        )
    )
    response = await user_transport.send(init_frame)
    assert response is not None, "Failed to send initial message"
    bot_chat_id = response.metadata.chat_id
    
    # Register command handlers on bot
    received_commands = []
    async def handle_command(frame: CommandFrame):
        logger.info(f"[BOT] Received command: {frame.command} with args: {frame.args}")
        received_commands.append(frame)
        # Send response back
        response = TextFrame(
            text=f"Command {frame.command} received with args: {frame.args}",
            metadata=EventMetadata(
                chat_id=frame.metadata.chat_id,
                chat_title=frame.metadata.chat_title,
                sender_id=frame.metadata.sender_id,
                sender_name=frame.metadata.sender_name,
                message_id=0
            )
        )
        await bot_transport.send(response)
    
    # Register commands without leading slash
    await bot_transport.register_command("start", handle_command)
    await bot_transport.register_command("status", handle_command)
    await bot_transport.register_command("config", handle_command)
    
    # Send commands from user to bot
    commands = [
        ("start", []),
        ("status", ["--verbose"]),
        ("config", ["key=value"])
    ]
    
    for command, args in commands:
        # Send command with slash
        logger.info(f"[USER] Sending command: /{command} with args: {args}")
        await user_transport.send(TextFrame(
            text=f"/{command} {' '.join(args)}".strip(),
            metadata=EventMetadata(
                chat_id=bot_chat_id,
                chat_title=None,
                sender_id=None,
                sender_name=None,
                message_id=0
            )
        ))
        # Wait for command to be processed
        await asyncio.sleep(1)
    
    # Wait for all commands to be processed
    await asyncio.sleep(2)
    
    # Verify commands were received
    assert len(received_commands) == len(commands), "Not all commands were received"
    for i, (command, args) in enumerate(commands):
        # Strip slash from received command for comparison
        received_cmd = received_commands[i].command.lstrip('/')
        assert received_cmd == command, f"Expected command '{command}', got '{received_cmd}'"
        assert received_commands[i].args == args, f"Expected args {args}, got {received_commands[i].args}"
    
    # Verify logs
    assert any("[USER] Sending command: /start" in record.message for record in caplog.records)
    assert any("[USER] Sending command: /status" in record.message for record in caplog.records)
    assert any("[USER] Sending command: /config" in record.message for record in caplog.records)
    assert any("[BOT] Received command: /start" in record.message for record in caplog.records)
    assert any("[BOT] Received command: /status" in record.message for record in caplog.records)
    assert any("[BOT] Received command: /config" in record.message for record in caplog.records)

@pytest.mark.asyncio
async def test_bot_sends_command_to_user(user_transport: TelegramUserTransport, bot_transport: TelegramBotTransport, caplog):
    """Test sending commands from bot to user."""
    # Get bot chat ID - we need to start a chat first to get user's chat ID
    bot_info = await bot_transport.app.bot.get_me()
    bot_username = bot_info.username

    # Set up a future to store the chat ID
    chat_id_future = asyncio.Future()

    # Add a message handler to capture the chat ID
    async def message_handler(update, context):
        if not chat_id_future.done():
            chat_id_future.set_result(update.message.chat.id)
    
    from telegram.ext import MessageHandler, filters
    bot_transport.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Send initial message to create chat
    init_frame = TextFrame(
        text="Hello bot!",
        metadata=EventMetadata(
            chat_id=f"@{bot_username}",
            chat_title=None,
            sender_id=None,
            sender_name=None,
            message_id=0
        )
    )
    response = await user_transport.send(init_frame)
    assert response is not None, "Failed to send initial message"

    # Wait for chat ID with timeout
    try:
        user_chat_id = await asyncio.wait_for(chat_id_future, timeout=2.0)
    except asyncio.TimeoutError:
        assert False, "Timed out waiting for chat ID"

    # Register command handlers for the user transport
    received_commands = []
    async def handle_command(frame: CommandFrame):
        received_commands.append(frame.command)

    await user_transport.register_command("start", handle_command)
    await user_transport.register_command("status", handle_command)
    await user_transport.register_command("config", handle_command)

    # Send commands from bot to user
    commands = ["start", "status", "config"]
    for cmd in commands:
        frame = TextFrame(
            text=f"/{cmd}",
            metadata=EventMetadata(
                chat_id=str(user_chat_id),
                chat_title=None,
                sender_id=None,
                sender_name=None,
                message_id=0
            )
        )
        await bot_transport.send(frame)
        await asyncio.sleep(0.2)  # Short wait between commands

    # Wait for all commands to be processed
    await asyncio.sleep(1.0)  # Longer wait to ensure commands are processed

    # Verify all commands were received
    assert len(received_commands) == len(commands), f"Not all commands were received. Expected {len(commands)}, got {len(received_commands)}"
    assert all(f"/{cmd}" in received_commands for cmd in commands), "Some commands were not received" 