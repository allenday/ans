import pytest
from chronicler.scribe.interface import ScribeConfig, UserSession, GroupConfig

@pytest.fixture
def test_config():
    """Provides a test scribe configuration"""
    return ScribeConfig(
        token="test_token",
        admin_users=[123],
        github_token=None,
        github_repo=None
    )

@pytest.fixture
def test_session():
    """Provides a test user session"""
    return UserSession(user_id=123)

@pytest.fixture
def test_group():
    """Provides a test group configuration"""
    return GroupConfig(
        group_id=456,
        topic_id="test_topic"
    ) 