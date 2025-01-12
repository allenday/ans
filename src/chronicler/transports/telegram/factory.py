"""Telegram transport factory."""
import logging
from typing import Optional

from chronicler.transports.telegram.bot import TelegramBotTransport
from chronicler.transports.telegram.user import TelegramUserTransport
from chronicler.transports.base import BaseTransport

logger = logging.getLogger(__name__)

class TelegramTransportFactory:
    """Factory for creating Telegram transports."""
    
    def create_transport(
        self,
        bot_token: Optional[str] = None,
        api_id: Optional[str] = None,
        api_hash: Optional[str] = None,
        phone_number: Optional[str] = None,
        session_name: Optional[str] = None
    ) -> BaseTransport:
        """Create a Telegram transport.
        
        Args:
            bot_token: Bot token for bot transport
            api_id: API ID for user transport
            api_hash: API hash for user transport
            phone_number: Phone number for user transport
            session_name: Session name for user transport (default: "chronicler")
        
        Returns:
            A Telegram transport instance
            
        Raises:
            ValueError: If invalid parameter combination is provided
        """
        logger.debug("Creating Telegram transport")
        
        # Check for invalid parameter combinations
        has_bot_token = bool(bot_token)
        has_user_creds = all([api_id, api_hash, phone_number])
        
        if has_bot_token and has_user_creds:
            logger.error("Cannot provide both bot_token and user credentials")
            raise ValueError("Cannot provide both bot_token and user credentials")
        
        if not has_bot_token and not has_user_creds:
            logger.error("Must provide either bot_token or (api_id, api_hash, phone_number)")
            raise ValueError("Must provide either bot_token or (api_id, api_hash, phone_number)")
        
        # Create appropriate transport
        if has_bot_token:
            logger.info("Creating TelegramBotTransport")
            return TelegramBotTransport(token=bot_token)
        else:
            logger.info("Creating TelegramUserTransport")
            return TelegramUserTransport(
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone_number,
                session_name=session_name or "chronicler"
            ) 