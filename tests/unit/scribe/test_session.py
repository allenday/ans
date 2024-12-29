import pytest
from unittest.mock import Mock, AsyncMock
from telegram import Message, Chat, User
from chronicler.scribe.core import Scribe
from chronicler.scribe.interface import UserSession, UserState

def create_message_update(text: str):
    """Helper to create message updates"""
    update = Mock()
    message = Mock(spec=Message)
    message.text = text
    update.message = message
    return update 