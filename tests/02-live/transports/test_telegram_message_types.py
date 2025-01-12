"""Live tests for Telegram message types in both directions."""
import pytest
import os
import asyncio
from pathlib import Path
from chronicler.frames.media import TextFrame

@pytest.fixture
def test_group_id():
    """Get test group ID from environment."""
    group_id = os.getenv('TELEGRAM_TEST_GROUP_ID')
    if not group_id:
        pytest.skip("TELEGRAM_TEST_GROUP_ID not set")
    return group_id

@pytest.fixture
def test_topic_id():
    """Get test topic ID from environment."""
    topic_id = os.getenv('TELEGRAM_TEST_TOPIC_ID')
    if not topic_id:
        pytest.skip("TELEGRAM_TEST_TOPIC_ID not set")
    return topic_id

@pytest.mark.asyncio
async def test_bidirectional_text_messages(
    user_transport,
    bot_transport,
    storage_processor,
    test_group_id,
    test_topic_id
):
    """Test sending and receiving text messages between user and bot."""
    # Get transport instances from async generators
    user = await anext(user_transport)
    bot = await anext(bot_transport)
    storage = await anext(storage_processor)
    
    # Create test messages
    user_message = "Test message from user"
    bot_message = "Test message from bot"
    
    # Create frames
    user_frame = TextFrame(
        content=user_message,
        metadata={
            'chat_id': test_group_id,
            'thread_id': test_topic_id,
            'direction': 'outgoing'
        }
    )
    
    bot_frame = TextFrame(
        content=bot_message,
        metadata={
            'chat_id': test_group_id,
            'thread_id': test_topic_id,
            'direction': 'outgoing'
        }
    )
    
    # Send messages
    await user.send(user_frame)
    await bot.send(bot_frame)
    
    # Wait for messages to be processed
    await asyncio.sleep(2)
    
    # Verify messages were stored
    # TODO: Add verification once storage query API is implemented

@pytest.mark.asyncio
async def test_message_reply_chain(
    user_transport,
    bot_transport,
    storage_processor,
    test_group_id,
    test_topic_id
):
    """Test message reply chain between user and bot."""
    # Get transport instances from async generators
    user = await anext(user_transport)
    bot = await anext(bot_transport)
    storage = await anext(storage_processor)
    
    # Send initial message from user
    user_frame1 = TextFrame(
        content="Initial message from user",
        metadata={
            'chat_id': test_group_id,
            'thread_id': test_topic_id,
            'direction': 'outgoing'
        }
    )
    await user.send(user_frame1)
    await asyncio.sleep(1)
    
    # Bot replies to user's message
    bot_frame = TextFrame(
        content="Bot reply to user",
        metadata={
            'chat_id': test_group_id,
            'thread_id': test_topic_id,
            'direction': 'outgoing',
            'reply_to_message_id': user_frame1.metadata.get('message_id')
        }
    )
    await bot.send(bot_frame)
    await asyncio.sleep(1)
    
    # User replies to bot's message
    user_frame2 = TextFrame(
        content="User reply to bot",
        metadata={
            'chat_id': test_group_id,
            'thread_id': test_topic_id,
            'direction': 'outgoing',
            'reply_to_message_id': bot_frame.metadata.get('message_id')
        }
    )
    await user.send(user_frame2)
    await asyncio.sleep(1)
    
    # TODO: Add verification once storage query API is implemented

@pytest.mark.asyncio
async def test_message_direction_metadata(
    user_transport,
    bot_transport,
    storage_processor,
    test_group_id,
    test_topic_id
):
    """Test that message direction is properly recorded in metadata."""
    # Get transport instances from async generators
    user = await anext(user_transport)
    bot = await anext(bot_transport)
    storage = await anext(storage_processor)
    
    # Send message from user
    user_frame = TextFrame(
        content="Message from user",
        metadata={
            'chat_id': test_group_id,
            'thread_id': test_topic_id,
            'direction': 'outgoing'
        }
    )
    await user.send(user_frame)
    
    # Send message from bot
    bot_frame = TextFrame(
        content="Message from bot",
        metadata={
            'chat_id': test_group_id,
            'thread_id': test_topic_id,
            'direction': 'outgoing'
        }
    )
    await bot.send(bot_frame)
    
    await asyncio.sleep(2)
    
    # TODO: Add verification of direction metadata once storage query API is implemented 