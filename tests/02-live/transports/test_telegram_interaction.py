"""Live tests for Telegram command interactions."""
import os
import pytest
import logging
import asyncio
import pytest_asyncio
from typing import AsyncGenerator
from telethon import events
from telegram.ext import MessageHandler, filters
from telegram.error import TimedOut

from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame
from chronicler.transports.telegram import TelegramTransportFactory
from chronicler.transports.events import EventMetadata

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_user_to_bot_interaction(user_transport, bot_transport, caplog):
    """Test sending commands from user to bot."""
    # Get transport instances from async generators
    user = await anext(user_transport)
    bot = await anext(bot_transport)
    
    test_group_id = int(os.environ["TELEGRAM_TEST_GROUP_ID"])
    test_group_name = os.environ["TELEGRAM_TEST_GROUP_NAME"]
    
    received_commands = []
    async def handle_command(frame: CommandFrame):
        logger.info(f"[BOT] Received command: {frame.command} with args: {frame.args}")
        received_commands.append(frame)
        response = TextFrame(
            content=f"Command {frame.command} received with args: {frame.args}",
            metadata=EventMetadata(
                chat_id=test_group_id,
                chat_title=test_group_name,
                sender_id=frame.metadata.sender_id,
                sender_name=frame.metadata.sender_name,
                message_id=0
            )
        )
        try:
            await bot.send(response)
            logger.info(f"[BOT] Response sent for command: {frame.command}")
        except TimedOut:
            logger.warning(f"[BOT] Timeout sending response for command: {frame.command}")
        except Exception as e:
            logger.error(f"[BOT] Error sending response for {frame.command}: {type(e).__name__}: {str(e)}")
    
    await bot.register_command("start", handle_command)
    await bot.register_command("status", handle_command)
    await bot.register_command("config", handle_command)
    
    commands = [
        ("/start", []),
        ("/status", ["--verbose"]),
        ("/config", ["key=value"])
    ]
    
    for command, args in commands:
        logger.info(f"[USER] Sending command: {command} with args: {args}")
        try:
            await user.send(TextFrame(
                content=f"{command} {' '.join(args)}".strip(),
                metadata=EventMetadata(
                    chat_id=test_group_id,
                    chat_title=test_group_name,
                    sender_id=None,
                    sender_name=None,
                    message_id=0
                )
            ))
            logger.info(f"[USER] Command sent successfully: {command}")
        except TimedOut:
            logger.warning(f"[USER] Timeout sending command: {command}")
        except Exception as e:
            logger.error(f"[USER] Error sending command {command}: {type(e).__name__}: {str(e)}")
        await asyncio.sleep(1)
    
    logger.info("[TEST] Waiting for commands to be processed...")
    await asyncio.sleep(2)
    
    logger.info(f"[TEST] Received {len(received_commands)} commands:")
    for cmd in received_commands:
        logger.info(f"[TEST] - {cmd.command} with args: {cmd.args}")
    
    assert len(received_commands) == len(commands), f"Not all commands were received. Expected {len(commands)}, got {len(received_commands)}"
    for i, (command, args) in enumerate(commands):
        assert received_commands[i].command == command
        assert received_commands[i].args == args
    
    assert any("[USER] Sending command: /start" in record.message for record in caplog.records)
    assert any("[USER] Sending command: /status" in record.message for record in caplog.records)
    assert any("[USER] Sending command: /config" in record.message for record in caplog.records)
    assert any("[BOT] Received command: /start" in record.message for record in caplog.records)
    assert any("[BOT] Received command: /status" in record.message for record in caplog.records)
    assert any("[BOT] Received command: /config" in record.message for record in caplog.records)

@pytest.mark.asyncio
async def test_transport_error_propagation(user_transport, bot_transport):
    """Test that transport errors are properly propagated."""
    # Get transport instances from async generators
    user = await anext(user_transport)
    bot = await anext(bot_transport)
    
    # Test sending to invalid chat ID
    with pytest.raises(Exception):
        await user.send(TextFrame(
            content="test message",
            metadata=EventMetadata(
                chat_id=-1,  # Invalid chat ID
                chat_title="Invalid Chat",
                sender_id=None,
                sender_name=None,
                message_id=0
            )
        ))

@pytest.mark.asyncio
async def test_transport_metadata_validation(user_transport, bot_transport):
    """Test metadata validation in transports."""
    # Get transport instances from async generators
    user = await anext(user_transport)
    bot = await anext(bot_transport)
    
    # Test sending without required metadata
    with pytest.raises(ValueError):
        await user.send(TextFrame(
            content="test message",
            metadata={}  # Missing required fields
        ))

@pytest.mark.asyncio
async def test_transport_lifecycle(user_transport, bot_transport):
    """Test transport lifecycle management."""
    # Get transport instances from async generators
    user = await anext(user_transport)
    bot = await anext(bot_transport)
    
    # Test stopping and restarting
    await user.stop()
    await bot.stop()
    
    await user.start()
    await bot.start()
    
    # Verify transports are working after restart
    test_group_id = int(os.environ["TELEGRAM_TEST_GROUP_ID"])
    test_group_name = os.environ["TELEGRAM_TEST_GROUP_NAME"]
    
    await user.send(TextFrame(
        content="test message after restart",
        metadata=EventMetadata(
            chat_id=test_group_id,
            chat_title=test_group_name,
            sender_id=None,
            sender_name=None,
            message_id=0
        )
    ))