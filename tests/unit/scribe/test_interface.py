import pytest
from chronicler.scribe.interface import (
    UserState, ScribeConfig, UserSession, GroupConfig, MessageConverter
)
from chronicler.storage.interface import Message, Attachment

@pytest.mark.unit
@pytest.mark.scribe
def test_user_state_transitions():
    """Test valid user state transitions"""
    assert UserState.IDLE.value < UserState.AWAITING_GITHUB_TOKEN.value
    assert UserState.AWAITING_GITHUB_TOKEN.value < UserState.AWAITING_GITHUB_REPO.value
    assert UserState.AWAITING_GITHUB_REPO.value < UserState.CONFIGURING_GROUP.value

@pytest.mark.unit
@pytest.mark.scribe
def test_scribe_config_validation():
    """Test scribe configuration validation"""
    # Valid config
    config = ScribeConfig(token="valid_token", admin_users=[123])
    assert config.token == "valid_token"
    
    # Invalid config
    with pytest.raises(ValueError):
        ScribeConfig(token="", admin_users=[])  # Empty token
    
    with pytest.raises(ValueError):
        ScribeConfig(token="valid_token", admin_users=[])  # No admins

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

@pytest.mark.scribe
@pytest.mark.asyncio
async def test_message_conversion():
    """Test converting Telegram message to storage format"""
    # [test code remains the same] 