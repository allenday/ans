"""Telegram transport factory."""
from typing import Optional, Union

from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from chronicler.transports.telegram_user_transport import TelegramUserTransport
from chronicler.transports.telegram_transport import TelegramTransportBase

class TelegramTransportFactory:
    """Factory for creating Telegram transports."""

    @classmethod
    def create_transport(cls, bot_token: str = None, api_id: str = None, api_hash: str = None, phone_number: str = None, session_name: str = None) -> TelegramTransportBase:
        """Create a transport instance based on provided parameters."""
        # Validate parameters if provided
        if api_id == 0 or api_id == "":
            raise ValueError("API ID cannot be empty")
        if api_hash == "":
            raise ValueError("API hash cannot be empty")
        if phone_number == "":
            raise ValueError("Phone number cannot be empty")
        if bot_token == "":
            raise ValueError("Bot token cannot be empty")

        # Check that either bot token or complete user credentials are provided
        if bot_token:
            if any([api_id, api_hash, phone_number]):
                raise ValueError("Cannot provide both bot token and user credentials")
            return cls.create_bot_transport(bot_token)
        elif all([api_id, api_hash, phone_number]):
            return cls.create_user_transport(api_id, api_hash, phone_number, session_name)
        else:
            raise ValueError("Must provide either bot token or complete user credentials")

    @staticmethod
    def create_bot_transport(token: str) -> TelegramBotTransport:
        """Create a bot transport instance."""
        return TelegramBotTransport(token=token)
        
    @staticmethod
    def create_user_transport(api_id: int, api_hash: str, phone_number: str, session_name: str = "user") -> TelegramUserTransport:
        """Create a new user transport.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone_number: User's phone number
            session_name: Name of the session file
            
        Returns:
            A new user transport
        """
        return TelegramUserTransport(
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            session_name=session_name
        ) 