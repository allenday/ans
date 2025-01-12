"""Telegram-specific attachment handling."""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from chronicler.logging import get_logger

from chronicler.storage.interface import Message, Attachment

logger = get_logger(__name__)

@dataclass
class AttachmentInfo:
    """Information about how to store an attachment."""
    category: str  # e.g., 'sticker', 'photo'
    format: str    # e.g., 'tgs', 'webp', 'jpg'
    filename: str  # e.g., 'abc123.tgs'
    path_parts: Tuple[str, ...]  # e.g., ('sticker_pack_name', 'abc123.tgs')

class TelegramAttachmentHandler:
    """Handles Telegram-specific attachment logic."""
    
    def get_attachment_info(self, message: Message, attachment: Attachment) -> AttachmentInfo:
        """Get attachment storage information."""
        try:
            logger.info("TG - Getting attachment info")
            # Handle stickers
            if message.metadata.get('sticker_set'):
                logger.debug(f"TG - Processing sticker from set: {message.metadata['sticker_set']}")
                format = message.metadata['format']  # tgs/webp/webm from transport
                filename = f"{message.metadata['file_unique_id']}.{format}"
                info = AttachmentInfo(
                    category='sticker',
                    format=format,
                    filename=filename,
                    path_parts=(message.metadata['sticker_set'], filename)
                )
                logger.debug(f"TG - Created sticker info: category={info.category}, format={info.format}")
                return info
                
            # Handle regular attachments
            logger.debug("TG - Processing regular attachment")
            format = message.metadata.get('format')
            if not format:
                # Fallback to MIME type subtype
                format = attachment.type.split('/')[-1]
                if format.startswith('x-'):
                    format = format[2:]
                # Clean up common MIME subtypes
                if format == 'jpeg':
                    format = 'jpg'
                logger.debug(f"TG - Determined format from MIME type: {format}")
                    
            # Use original filename if available, otherwise fallback to ID
            if attachment.filename:
                filename = attachment.filename
                logger.debug(f"TG - Using original filename: {filename}")
            else:
                filename = f"{attachment.id}.{format}"
                logger.debug(f"TG - Using generated filename: {filename}")
                
            info = AttachmentInfo(
                category=format,
                format=format,
                filename=filename,
                path_parts=(filename,)
            )
            logger.debug(f"TG - Created attachment info: category={info.category}, format={info.format}")
            return info
        except Exception as e:
            logger.error(f"TG - Failed to get attachment info: {e}", exc_info=True)
            raise
        
    def update_message_content(self, message: Message) -> None:
        """Update message content based on Telegram-specific rules."""
        try:
            logger.info("TG - Updating message content")
            # Use emoji as content for stickers
            if message.metadata.get('sticker_set') and message.metadata.get('emoji'):
                logger.debug(f"TG - Setting sticker emoji content: {message.metadata['emoji']}")
                message.content = message.metadata['emoji']
            else:
                logger.debug("TG - No content update needed")
        except Exception as e:
            logger.error(f"TG - Failed to update message content: {e}", exc_info=True)
            raise
            
    def get_attachment_path_str(self, info: AttachmentInfo) -> str:
        """Get the relative path string for the attachment."""
        try:
            logger.debug(f"TG - Getting path string for: category={info.category}, parts={info.path_parts}")
            path = str(Path('attachments') / info.category / Path(*info.path_parts))
            logger.debug(f"TG - Generated path: {path}")
            return path
        except Exception as e:
            logger.error(f"TG - Failed to get attachment path string: {e}", exc_info=True)
            raise 