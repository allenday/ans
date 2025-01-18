"""Live tests for Telegram interactions."""
import os
import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator

from chronicler.logging import get_logger, configure_logging
from chronicler.frames.media import TextFrame
from chronicler.transports.telegram_factory import (
    TelegramTransportFactory,
    TelegramUserTransport,
    TelegramBotTransport
)
from chronicler.transports.events import EventMetadata

logger = get_logger(__name__)

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Set up logging for all tests."""
    configure_logging(level='DEBUG')
    caplog.set_level('DEBUG')
    yield

@pytest.mark.asyncio(loop_scope="function")
async def test_user_to_bot_text_exchange(user_transport: TelegramUserTransport, test_bot_transport: TelegramBotTransport, caplog):
    """Test sending commands from user to bot."""
    test_group_id = int(os.environ["TELEGRAM_TEST_GROUP_ID"])
    test_group_name = os.environ["TELEGRAM_TEST_GROUP_NAME"]
    
    received_commands = []
    async def handle_command(frame: CommandFrame):
        logger.info(f"[BOT] Received command: {frame.command} with args: {frame.args}")
        received_commands.append(frame)
        response = TextFrame(
            text=f"Command {frame.command} received with args: {frame.args}",
            metadata=EventMetadata(
                chat_id=test_group_id,
                chat_title=test_group_name,
                sender_id=frame.metadata.sender_id,
                sender_name=frame.metadata.sender_name,
                message_id=0
            )
        )
        try:
            await test_bot_transport.send(response)
            logger.info(f"[BOT] Response sent for command: {frame.command}")
        except TimedOut:
            logger.warning(f"[BOT] Timeout sending response for command: {frame.command}")
        except Exception as e:
            logger.error(f"[BOT] Error sending response for {frame.command}: {type(e).__name__}: {str(e)}")
    
    await test_bot_transport.register_command("start", handle_command)
    await test_bot_transport.register_command("status", handle_command)
    await test_bot_transport.register_command("config", handle_command)
    
    commands = [
        ("/start", []),
        ("/status", ["--verbose"]),
        ("/config", ["key=value"])
    ]
    
    for command, args in commands:
        logger.info(f"[USER] Sending command: {command} with args: {args}")
        try:
            await user_transport.send(TextFrame(
                text=f"{command} {' '.join(args)}".strip(),
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