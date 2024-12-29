import pytest
from chronicler.scribe.interface import (
    UserState, ScribeConfig, UserSession, GroupConfig, MessageConverter
)
from chronicler.storage.interface import Message, Attachment
from datetime import datetime

@pytest.fixture
def test_session():
    """Create a test user session"""
    return UserSession(user_id=123)

@pytest.fixture
def test_group():
    """Create a test group config"""
    return GroupConfig(group_id=123, topic_id="test_topic", enabled=True)

@pytest.fixture
def test_config():
    """Create a test scribe config"""
    return ScribeConfig(telegram_token="test_token")

@pytest.mark.unit
@pytest.mark.scribe
def test_user_state_transitions():
    """Test user state transitions"""
    # Test initial state
    session = UserSession(user_id=123)
    assert session.state == UserState.IDLE
    
    # Test state changes
    session.state = UserState.AWAITING_GITHUB_TOKEN
    assert session.state == UserState.AWAITING_GITHUB_TOKEN
    
    session.state = UserState.AWAITING_GITHUB_REPO
    assert session.state == UserState.AWAITING_GITHUB_REPO
    
    session.state = UserState.IDLE
    assert session.state == UserState.IDLE

@pytest.mark.unit
@pytest.mark.scribe
def test_scribe_config_validation():
    """Test that ScribeConfig validates token correctly"""
    # Test missing token
    with pytest.raises(ValueError, match="Either telegram_token or token must be provided"):
        ScribeConfig()
    
    # Test with telegram_token
    config = ScribeConfig(telegram_token="test_token")
    assert config.telegram_token == "test_token"
    assert config.token == "test_token"  # Both should be set
    
    # Test with token alias
    config = ScribeConfig(token="test_token")
    assert config.telegram_token == "test_token"
    assert config.token == "test_token"

@pytest.mark.unit
@pytest.mark.scribe
def test_user_session_context(test_session):
    """Test user session context management"""
    # Default empty context
    assert test_session.context == {}
    
    # Context updates
    test_session.context["key"] = "value"
    assert test_session.context["key"] == "value"
    
    # Context isolation
    other_session = UserSession(user_id=456)
    assert "key" not in other_session.context

@pytest.mark.unit
@pytest.mark.scribe
def test_group_config_filters(test_group):
    """Test group configuration filters"""
    # Default empty filters
    assert test_group.filters == {}
    
    # Add filters
    test_group.filters.update({
        "media_only": True,
        "min_length": 10
    })
    assert test_group.filters["media_only"] is True
    assert test_group.filters["min_length"] == 10

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_message_conversion():
    """Test converting Telegram message to storage format"""
    # Create test message
    message = Message(
        content="Test message",
        source="telegram_123",
        metadata={
            "type": "text",
            "chat_id": 456,
            "message_id": 789
        },
        timestamp=datetime.utcnow()
    )
    
    # Convert message
    converter = MessageConverter()
    storage_message = Message(
        content=message.content,
        source=message.source,
        metadata=message.metadata,
        timestamp=message.timestamp
    )
    
    # Verify conversion
    assert storage_message.content == "Test message"
    assert storage_message.source == "telegram_123"
    assert storage_message.metadata["chat_id"] == 456
    assert storage_message.metadata["type"] == "text" 