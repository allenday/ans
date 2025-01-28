"""Unit tests for TelegramUserTransport."""
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, Mock, patch
from datetime import datetime, timezone
from telethon.errors.rpcerrorlist import ApiIdInvalidError

from chronicler.frames.base import Frame
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame
from chronicler.transports.events import EventMetadata
from chronicler.transports.telegram.transport.user import TelegramUserTransport
from chronicler.transports.telegram_user_update import TelegramUserUpdate
from chronicler.transports.telegram_user_event import TelegramUserEvent
from chronicler.exceptions import TransportError, TransportAuthenticationError
from chronicler.logging import get_logger

logger = get_logger(__name__, component='test.transports.telegram')

@pytest_asyncio.fixture
async def mock_client():
    """Create a mock client."""
    mock = AsyncMock()
    mock.connect = AsyncMock(return_value=True)
    mock.disconnect = AsyncMock()
    mock.is_connected = AsyncMock(return_value=True)
    mock.is_user_authorized = AsyncMock(return_value=True)
    mock.send_code_request = AsyncMock()
    mock.sign_in = AsyncMock()
    mock.get_me = AsyncMock(return_value=Mock(id=123, first_name="Test User"))
    mock.add_event_handler = AsyncMock()
    mock.run_until_disconnected = AsyncMock()
    return mock

@pytest_asyncio.fixture
async def transport(mock_client):
    """Create a transport instance with mock client."""
    with patch('chronicler.transports.telegram.transport.user.TelegramClient', return_value=mock_client):
        transport = TelegramUserTransport("123", "hash", "+1234567890", session_name=":memory:")
        mock_client.is_user_authorized.return_value = True  # Ensure client is authorized
        mock_client.connect.return_value = True  # Ensure connection succeeds
        
        # Set up message sender mock
        mock_sender = AsyncMock()
        mock_sender.send = AsyncMock()
        transport._message_sender = mock_sender
        
        # Initialize transport
        transport._initialized = True
        transport._client = mock_client
        
        await transport.start()
        yield transport
        await transport.stop()
        if hasattr(transport, '_client') and transport._client:
            await transport._client.disconnect()

@pytest.mark.asyncio
async def test_user_transport_validates_params():
    """Test parameter validation during initialization."""
    # All parameters empty
    with pytest.raises(TransportAuthenticationError, match="API ID, API hash and phone number cannot be empty"):
        TelegramUserTransport(api_id="", api_hash="", phone_number="")

    # Missing API hash
    with pytest.raises(TransportAuthenticationError, match="API ID, API hash and phone number cannot be empty"):
        TelegramUserTransport(api_id="123", api_hash="", phone_number="+1234567890")

    # Missing phone number
    with pytest.raises(TransportAuthenticationError, match="API ID, API hash and phone number cannot be empty"):
        TelegramUserTransport(api_id="123", api_hash="abc", phone_number="")

@pytest.mark.asyncio
@patch('chronicler.transports.telegram.transport.user.TelegramClient')
async def test_user_transport_auth_error(mock_client):
    """Test error handling during transport authentication."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )

    # Mock client to raise an authentication error
    client_instance = AsyncMock()
    client_instance.connect = AsyncMock()
    client_instance.is_user_authorized = AsyncMock(return_value=False)
    client_instance.send_code_request = AsyncMock()
    mock_client.return_value = client_instance

    # Start should raise TransportAuthenticationError
    with pytest.raises(TransportAuthenticationError, match="User not authorized"):
        await transport.start()

@pytest.mark.asyncio
async def test_user_transport_api_error():
    """Test handling of invalid API credentials."""
    # Mock client to raise API error
    mock_client = AsyncMock()
    mock_client.connect.side_effect = ApiIdInvalidError("The api_id/api_hash combination is invalid")
    
    with patch('chronicler.transports.telegram.transport.user.TelegramClient', return_value=mock_client):
        transport = TelegramUserTransport(
            api_id="123",
            api_hash="invalid_hash",
            phone_number="+1234567890",
            session_name=":memory:"
        )
        
        with pytest.raises(TransportError, match="The api_id/api_hash combination is invalid"):
            await transport.start()

@pytest.mark.asyncio
async def test_user_transport_send_without_init():
    """Test sending frame without initializing transport."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )

    frame = TextFrame(
        content="Test message",
        metadata=EventMetadata(
            chat_id=67890,
            chat_title="Test Chat",
            thread_id="22222"
        )
    )

    with pytest.raises(RuntimeError, match="Transport not initialized"):
        await transport.send(frame)

@pytest.mark.asyncio
@patch('chronicler.transports.telegram.transport.user.TelegramClient')
async def test_user_handle_text_message(mock_client):
    """Test handling text messages."""
    # Setup mock client
    mock_client_instance = AsyncMock()
    mock_client_instance.connect = AsyncMock(return_value=True)
    mock_client_instance.is_connected = AsyncMock(return_value=True)
    mock_client_instance.is_user_authorized = AsyncMock(return_value=True)
    mock_client_instance.get_me = AsyncMock(return_value=Mock(id=123, first_name="Test User"))
    mock_client_instance.start = AsyncMock()
    mock_client.return_value = mock_client_instance

    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )

    # Initialize transport
    await transport.start()
    transport._initialized = True

    # Create mock update with proper structure
    mock_chat = MagicMock()
    mock_chat.id = 67890
    mock_chat.title = "Test Chat"
    mock_chat.type = "private"

    mock_sender = MagicMock()
    mock_sender.id = 11111
    mock_sender.username = "testuser"

    mock_message = MagicMock()
    mock_message.text = "Hello world"
    mock_message.chat = mock_chat
    mock_message.sender = mock_sender
    mock_message.id = 12345
    mock_message.reply_to_msg_id = 22222
    mock_message.date = datetime(2024, 1, 1, tzinfo=timezone.utc)

    mock_event = MagicMock()
    mock_event.message = mock_message

    # Create TelegramUserUpdate wrapper
    update = TelegramUserUpdate(mock_event)

    # Track processed frames
    processed_frames = []
    async def frame_processor(frame):
        processed_frames.append(frame)
        frame.content = frame.content.upper()
        return frame
    transport.frame_processor = frame_processor

    # Handle message
    await transport._handle_message(update)

    # Verify frame was processed
    assert len(processed_frames) == 1
    frame = processed_frames[0]
    assert isinstance(frame, TextFrame)
    assert frame.content == "HELLO WORLD"
    assert frame.metadata['chat_id'] == 67890

    # Clean up
    await transport.stop()

@pytest.mark.asyncio
@patch('chronicler.transports.telegram.transport.user.TelegramClient')
async def test_user_handle_command(mock_client):
    """Test that command registration is no longer supported."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )

    # Verify that command registration raises NotImplementedError
    with pytest.raises(NotImplementedError) as exc_info:
        await transport.register_command("/start", AsyncMock())
    assert str(exc_info.value) == "Command registration is no longer supported in Transport"

@pytest.mark.asyncio
@patch('chronicler.transports.telegram.transport.user.TelegramClient')
async def test_user_transport_send_error(mock_client):
    """Test error handling during frame sending."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )

    # Mock client and message sender
    client_instance = AsyncMock()
    client_instance.start = AsyncMock()
    mock_client.return_value = client_instance

    # Mock message sender
    mock_sender = AsyncMock()
    mock_sender.send = AsyncMock(side_effect=Exception("Failed to send message"))
    transport._message_sender = mock_sender
    transport._initialized = True

    # Create a test frame with metadata
    metadata = EventMetadata(
        chat_id=67890,
        chat_title="Test Chat",
        thread_id="22222"
    )
    frame = TextFrame(content="Test message", metadata=metadata)

    # Send should raise TransportError
    with pytest.raises(TransportError, match="Failed to send message"):
        await transport.send(frame)

@pytest.mark.asyncio
@patch('chronicler.transports.telegram.transport.user.TelegramClient')
async def test_user_send_text_frame(mock_client):
    """Test sending text frame."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )

    # Mock client and message sender
    client_instance = AsyncMock()
    client_instance.start = AsyncMock()
    mock_client.return_value = client_instance

    # Mock message sender
    mock_sender = AsyncMock()
    mock_sender.send = AsyncMock(return_value=123)  # Return message ID
    transport._message_sender = mock_sender
    transport._initialized = True

    # Create a test frame with metadata
    metadata = EventMetadata(
        chat_id=67890,
        chat_title="Test Chat",
        thread_id="22222"
    )
    frame = TextFrame(content="Test message", metadata=metadata)

    # Send frame
    result = await transport.send(frame)
    assert result == 123  # Assert that result is the message ID

@pytest.mark.asyncio
@patch('chronicler.transports.telegram.transport.user.TelegramClient')
async def test_user_send_unsupported_frame(mock_client):
    """Test sending unsupported frame type."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )

    # Mock client and message sender
    client_instance = AsyncMock()
    client_instance.start = AsyncMock()
    mock_client.return_value = client_instance

    # Mock message sender
    mock_sender = AsyncMock()
    mock_sender.send = AsyncMock(side_effect=Exception("Unsupported frame type"))
    transport._message_sender = mock_sender
    transport._initialized = True

    # Create a test frame with metadata
    metadata = EventMetadata(
        chat_id=67890,
        chat_title="Test Chat",
        thread_id="22222"
    )
    frame = Frame(metadata=metadata)  # Base frame type is not supported

    # Send should raise TransportError
    with pytest.raises(TransportError, match="Unsupported frame type"):
        await transport.send(frame)

@pytest.mark.asyncio
async def test_user_transport_lifecycle():
    """Test user transport lifecycle."""
    with patch('chronicler.transports.telegram.transport.user.TelegramClient') as mock_client_class:
        # Setup mock client
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        mock_client.is_connected = AsyncMock(return_value=True)
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.send_code_request = AsyncMock()
        mock_client.sign_in = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=Mock(id=123, first_name="Test User"))
        mock_client.add_event_handler = AsyncMock()
        
        # Mock the start method to avoid actual client initialization
        mock_client.start = AsyncMock()
        mock_client_class.return_value = mock_client
        
        transport = TelegramUserTransport(
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890",
            session_name=":memory:"
        )
        
        # Start transport and verify initialization
        await transport.start()
        assert mock_client.connect.called
        assert mock_client.is_user_authorized.called
        assert mock_client.get_me.called
        assert transport._message_sender is not None
        assert transport._initialized is True
        
        # Stop transport and verify cleanup
        await transport.stop()
        mock_client.disconnect.assert_awaited_once()

@pytest.mark.asyncio
@patch('chronicler.transports.telegram.transport.user.TelegramClient')
async def test_user_transport_send_image(mock_client):
    """Test sending image frame."""
    transport = TelegramUserTransport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890",
        session_name=":memory:"
    )

    # Mock client and message sender
    client_instance = AsyncMock()
    client_instance.start = AsyncMock()
    mock_client.return_value = client_instance

    # Mock message sender
    mock_sender = AsyncMock()
    mock_sender.send = AsyncMock(return_value=123)  # Return message ID
    transport._message_sender = mock_sender
    transport._initialized = True

    # Create a test frame with metadata
    metadata = EventMetadata(
        chat_id=67890,
        chat_title="Test Chat",
        thread_id="22222"
    )
    frame = ImageFrame(
        content=b"Test image bytes",  # Provide bytes for image content
        caption="Test caption",
        metadata=metadata
    )

    # Send frame
    result = await transport.send(frame)
    assert result == 123  # Assert that result is the message ID

@pytest.mark.asyncio
async def test_user_transport_message_processing(transport, mock_client):
    """Test message handling with frame processing."""
    # Create mock message with ID
    mock_message = Mock()
    mock_message.id = 789
    transport._message_sender.send = AsyncMock(return_value=mock_message)

    # Create mock update
    mock_chat = MagicMock()
    mock_chat.id = 456
    mock_chat.title = "Test Chat"
    mock_chat.type = "private"

    mock_sender = MagicMock()
    mock_sender.id = 11111
    mock_sender.username = "testuser"

    mock_message = MagicMock()
    mock_message.text = "Hello, World!"
    mock_message.chat = mock_chat
    mock_message.sender = mock_sender
    mock_message.id = 789
    mock_message.reply_to_msg_id = None
    mock_message.date = datetime(2024, 1, 1, tzinfo=timezone.utc)

    mock_event = MagicMock()
    mock_event.message = mock_message

    # Create frame processor that converts text to uppercase
    async def frame_processor(frame):
        frame.content = frame.content.upper()
        return frame
    transport.frame_processor = frame_processor

    # Create update object and handle message
    update = TelegramUserUpdate(mock_event)
    await transport._handle_message(update)

    # Verify message was sent with processed text
    transport._message_sender.send.assert_awaited_once()
    args, kwargs = transport._message_sender.send.await_args
    frame = args[0]
    assert frame.content == "HELLO, WORLD!"

    # Clean up
    await transport.stop()

@pytest.mark.asyncio
async def test_user_transport_command_processing(mock_client):
    """Test that command registration is no longer supported."""
    transport = TelegramUserTransport("123", "hash", "+1234567890")
    transport._initialized = True  # Skip initialization since we're testing command registration

    # Verify that command registration raises NotImplementedError
    with pytest.raises(NotImplementedError) as exc_info:
        await transport.register_command("/test", AsyncMock())
    assert str(exc_info.value) == "Command registration is no longer supported in Transport"

@pytest.mark.asyncio
async def test_user_event_handling():
    """Test TelegramUserEvent functionality."""
    # Create mock update
    mock_update = Mock()
    mock_update.message_text = "/test arg1 arg2"
    mock_update.chat_id = 456
    mock_update.chat_title = "Test Chat"
    mock_update.sender_id = 123
    mock_update.sender_name = "Test User"
    mock_update.message_id = 789
    mock_update.thread_id = "thread1"
    mock_update.timestamp = 1234567890

    # Test initialization with dict metadata
    metadata_dict = {
        'chat_id': 456,
        'platform': 'telegram'
    }
    event = TelegramUserEvent(mock_update, metadata_dict)
    assert event.get_text() == "/test arg1 arg2"
    assert event.get_metadata().chat_id == 456
    assert event.get_metadata().platform == 'telegram'

    # Test initialization with EventMetadata
    metadata_obj = EventMetadata(chat_id=456, platform='telegram')
    event = TelegramUserEvent(mock_update, metadata_obj)
    assert event.get_text() == "/test arg1 arg2"
    assert event.get_metadata().chat_id == 456
    assert event.get_metadata().platform == 'telegram'

    # Test initialization without metadata
    event = TelegramUserEvent(mock_update)
    assert event.get_text() == "/test arg1 arg2"
    metadata = event.get_metadata()
    assert metadata.chat_id == 456
    assert metadata.chat_title == "Test Chat"
    assert metadata.sender_id == 123
    assert metadata.sender_name == "Test User"
    assert metadata.message_id == 789
    assert metadata.thread_id == "thread1"
    assert metadata.timestamp == 1234567890

    # Test command argument parsing
    assert event.get_command_args() == ["arg1", "arg2"]

    # Test with non-command message
    mock_update.message_text = "Hello, world!"
    event = TelegramUserEvent(mock_update)
    assert event.get_command_args() == []

    # Test with empty message
    mock_update.message_text = None
    event = TelegramUserEvent(mock_update)
    assert event.get_command_args() == []