import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from telegram.error import InvalidToken, NetworkError
from chronicler.transports.events import EventMetadata, TelegramBotEvent
from chronicler.transports.telegram_factory import (
    TelegramTransportFactory,
    TelegramTransportBase,
    TelegramUserTransport,
    TelegramBotTransport
)
from chronicler.frames.command import CommandFrame
from chronicler.frames.media import TextFrame, ImageFrame
import logging

def test_factory_creates_user_transport():
    """Test factory creates TelegramUserTransport when api_id and api_hash are provided."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    assert isinstance(transport, TelegramUserTransport)
    assert transport.api_id == "123"
    assert transport.api_hash == "abc"
    assert transport.phone_number == "+1234567890"

def test_factory_creates_bot_transport():
    """Test factory creates TelegramBotTransport when bot_token is provided."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(bot_token="BOT:TOKEN")
    
    assert isinstance(transport, TelegramBotTransport)
    assert transport.token == "BOT:TOKEN"

def test_factory_raises_error_on_missing_params():
    """Test factory raises ValueError when no parameters are provided."""
    factory = TelegramTransportFactory()
    
    with pytest.raises(ValueError, match=r"Must provide either bot_token or \(api_id, api_hash, phone_number\)"):
        factory.create_transport()

def test_factory_raises_error_on_both_params():
    """Test factory raises ValueError when both bot and user params are provided."""
    factory = TelegramTransportFactory()
    
    with pytest.raises(ValueError, match="Cannot provide both bot_token and user credentials"):
        factory.create_transport(
            bot_token="BOT:TOKEN",
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890"
        )

def test_factory_raises_error_on_partial_user_params():
    """Test factory raises ValueError when only some user params are provided."""
    factory = TelegramTransportFactory()
    
    with pytest.raises(ValueError, match=r"Must provide either bot_token or \(api_id, api_hash, phone_number\)"):
        factory.create_transport(api_id="123", api_hash="abc")  # Missing phone_number

def test_factory_uses_default_session_name():
    """Test factory uses default session name for user transport."""
    factory = TelegramTransportFactory()
    transport = factory.create_transport(
        api_id="123",
        api_hash="abc",
        phone_number="+1234567890"
    )
    
    assert isinstance(transport, TelegramUserTransport)
    assert transport.session_name == "chronicler"  # Default value

@patch('chronicler.transports.telegram_factory.TelegramClient')
def test_user_transport_initialization_error(mock_client):
    """Test error handling during user transport initialization."""
    mock_client.side_effect = Exception("Failed to initialize client")
    
    with pytest.raises(Exception, match="Failed to initialize client"):
        TelegramUserTransport(
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890"
        )

@pytest.fixture
def app():
    """Create a mock application for testing."""
    mock = MagicMock()
    mock.bot = MagicMock()
    mock.bot.base_url = MagicMock(return_value="https://api.telegram.org/bot")
    mock.bot.token = "test_token"
    mock.bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))
    mock.bot.send_photo = AsyncMock(return_value=MagicMock(message_id=123))
    return mock

@pytest.fixture
def transport(app):
    """Create a transport instance for testing."""
    transport = TelegramBotTransport(app)
    transport.logger = logging.getLogger("test")
    return transport

@pytest.mark.asyncio
async def test_bot_transport_initialization_error():
    """Test error handling during bot transport initialization."""
    transport = TelegramBotTransport("test_token")
    transport.logger = logging.getLogger("test")
    
    # Mock Application.builder() to raise InvalidToken
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_builder.return_value = MagicMock()
        mock_builder.return_value.token = MagicMock(return_value=mock_builder.return_value)
        mock_builder.return_value.build = AsyncMock(side_effect=InvalidToken("Invalid token"))
        with pytest.raises(InvalidToken, match="Invalid token"):
            await transport.start()

@pytest.mark.asyncio
async def test_bot_transport_command_registration():
    """Test command registration in bot transport."""
    transport = TelegramBotTransport("test_token")
    transport._app = MagicMock()
    transport._app.bot = MagicMock()
    transport._initialized = True

    # Register a command
    async def test_command(event: TelegramBotEvent) -> None:
        pass

    await transport.register_command("test", test_command)
    assert "/test" in transport._command_handlers

@pytest.mark.asyncio
async def test_bot_transport_command_execution():
    """Test command execution in bot transport."""
    transport = TelegramBotTransport("test_token")
    transport._app = MagicMock()
    transport._app.bot = MagicMock()
    transport._initialized = True

    # Register a command
    command_executed = False
    async def test_command(event: TelegramBotEvent) -> None:
        nonlocal command_executed
        command_executed = True

    await transport.register_command("test", test_command)

    # Create mock update and context
    update = MagicMock()
    update.message = MagicMock()
    update.message.chat_id = 123
    update.message.chat.title = "Test Chat"
    update.message.from_user = MagicMock()
    update.message.from_user.id = 456
    update.message.from_user.username = "Test User"
    update.message.text = "/test"
    update.message.message_id = 789

    context = MagicMock()
    context.args = []

    # Create a test event
    event = TelegramBotEvent(update, context)

    # Execute the command
    await transport.process_frame(CommandFrame(command="/test", args=[]))
    assert command_executed

@pytest.mark.asyncio
async def test_bot_transport_send_text():
    """Test sending text message through bot transport."""
    transport = TelegramBotTransport("test_token")
    transport.logger = logging.getLogger("test")
    
    # Mock the application after initialization
    transport._app = MagicMock()
    transport._app.bot = MagicMock()
    transport._app.bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))
    transport._initialized = True

    frame = TextFrame(content="Hello, world!", metadata=EventMetadata(chat_id=456))
    result = await transport.send(frame)

    transport._app.bot.send_message.assert_called_once_with(
        chat_id=456,
        text="Hello, world!"
    )
    assert result.metadata.message_id == 123

@pytest.mark.asyncio
async def test_bot_transport_send_image():
    """Test sending image messages through bot transport."""
    transport = TelegramBotTransport("test_token")
    transport.logger = logging.getLogger("test")
    
    # Mock the application after initialization
    transport._app = MagicMock()
    transport._app.bot = MagicMock()
    transport._app.bot.send_photo = AsyncMock(return_value=MagicMock(message_id=123))
    transport._initialized = True
    
    frame = ImageFrame(
        content=b"test image data",
        metadata=EventMetadata(chat_id=456)
    )
    
    result = await transport.send(frame)
    assert result.metadata.message_id == 123
    transport._app.bot.send_photo.assert_called_once_with(
        chat_id=456,
        photo=frame.content,
        caption=None
    )

@pytest.mark.asyncio
async def test_transport_send_error_handling():
    """Test error handling when sending messages fails."""
    transport = TelegramBotTransport("test_token")
    transport.logger = logging.getLogger("test")
    
    # Mock the application after initialization
    transport._app = MagicMock()
    transport._app.bot = MagicMock()
    transport._app.bot.send_message = AsyncMock(side_effect=NetworkError("Failed to send message"))
    transport._initialized = True
    
    frame = TextFrame(
        content="Hello, world!",
        metadata=EventMetadata(chat_id=456)
    )
    
    with pytest.raises(NetworkError, match="Failed to send message"):
        await transport.send(frame)

    transport._app.bot.send_message.assert_called_once_with(
        chat_id=456,
        text="Hello, world!"
    )

@pytest.mark.asyncio
async def test_user_transport_command_registration():
    """Test registering command handlers in user transport."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock_client:
        # Setup mock client
        client = MagicMock()
        client.connect = AsyncMock()
        client.is_user_authorized = AsyncMock(return_value=True)
        client.start = AsyncMock()
        mock_client.return_value = client
        
        # Create transport and register command
        transport = TelegramUserTransport(
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890"
        )
        
        async def test_handler(frame):
            pass
            
        await transport.register_command("/test", test_handler)
        
        # Verify command was registered
        assert "/test" in transport._command_handlers
        assert transport._command_handlers["/test"] == test_handler

@pytest.mark.asyncio
async def test_user_transport_command_execution():
    """Test executing registered command handlers in user transport."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock_client:
        # Setup mock client
        client = MagicMock()
        client.connect = AsyncMock()
        client.is_user_authorized = AsyncMock(return_value=True)
        client.start = AsyncMock()
        client.send_message = AsyncMock(return_value=MagicMock(id=123))
        mock_client.return_value = client

        # Create transport
        transport = TelegramUserTransport(
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890"
        )

        # Setup test handler
        handler_called = False
        async def test_handler(frame):
            nonlocal handler_called
            handler_called = True
            assert frame.command == "/test"
            assert frame.args == ["arg1", "arg2"]
            assert frame.metadata.chat_id == 123

        await transport.register_command("/test", test_handler)

        # Create test frame
        frame = CommandFrame(
            command="/test",
            args=["arg1", "arg2"],
            metadata=EventMetadata(chat_id=123)
        )

        await transport._handle_command(frame)
        assert handler_called

@pytest.mark.asyncio
async def test_user_transport_send_text():
    """Test sending text messages through user transport."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock_client:
        # Setup mock client
        client = MagicMock()
        client.connect = AsyncMock()
        client.is_user_authorized = AsyncMock(return_value=True)
        client.start = AsyncMock()
        client.send_message = AsyncMock(return_value=MagicMock(id=123))
        mock_client.return_value = client

        # Create transport
        transport = TelegramUserTransport(
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890"
        )

        # Create and send text frame
        frame = TextFrame(
            content="Hello, world!",
            metadata=EventMetadata(chat_id=456)
        )

        result = await transport.send(frame)
        assert result.metadata.message_id == 123
        client.send_message.assert_called_once_with(
            chat_id=456,
            text="Hello, world!"
        )

@pytest.mark.asyncio
async def test_user_transport_send_image():
    """Test sending image messages through user transport."""
    with patch('chronicler.transports.telegram_factory.TelegramClient') as mock_client:
        # Setup mock client
        client = MagicMock()
        client.connect = AsyncMock()
        client.is_user_authorized = AsyncMock(return_value=True)
        client.start = AsyncMock()
        client.send_file = AsyncMock(return_value=MagicMock(id=123))
        mock_client.return_value = client

        # Create transport
        transport = TelegramUserTransport(
            api_id="123",
            api_hash="abc",
            phone_number="+1234567890"
        )

        # Create and send image frame
        frame = ImageFrame(
            content=b"image data",
            metadata=EventMetadata(chat_id=456),
            caption="Test image"
        )

        result = await transport.send(frame)
        assert result.metadata.message_id == 123
        client.send_file.assert_called_once_with(456, file=b"image data", caption="Test image") 