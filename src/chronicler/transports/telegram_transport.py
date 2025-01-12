from typing import Optional

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters

from chronicler.frames.base import Frame
from chronicler.frames.media import TextFrame, ImageFrame, DocumentFrame, StickerFrame, AudioFrame, VoiceFrame
from chronicler.transports.base import BaseTransport
from chronicler.commands.frames import CommandFrame
from chronicler.logging import get_logger, trace_operation

logger = get_logger(__name__, component="telegram_transport")

class TelegramTransport(BaseTransport):
    """A transport for Telegram that converts Telegram messages to frames."""
    
    def __init__(self, token: str):
        super().__init__()
        logger.info("Initializing TelegramTransport")
        self.token = token
        self.app = Application.builder().token(token).build()
        
        # Add command handler first
        self.app.add_handler(CommandHandler(
            ["start", "config", "status"],
            self._handle_command
        ))
        logger.debug("Added command handlers")
        
        # Handle all other message types
        self.app.add_handler(MessageHandler(
            filters.ALL,  # Capture all message types
            self._handle_message
        ))
        logger.debug("Added message handler for all message types")
    
    @trace_operation('transport.telegram')
    async def start(self):
        """Start the Telegram bot and message handling."""
        logger.info("Starting Telegram transport")
        await self.app.initialize()
        logger.debug("Application initialized")
        
        # Get bot info
        bot = await self.app.bot.get_me()
        logger.info(f"Bot info: id={bot.id}, name={bot.first_name}, username={bot.username}")
        
        await self.app.start()
        logger.debug("Application started")
        await self.app.updater.start_polling(drop_pending_updates=False, allowed_updates=['message'])
        logger.info("Polling started - bot is ready to receive messages")
    
    @trace_operation('transport.telegram')
    async def stop(self):
        """Stop the Telegram bot."""
        logger.info("Stopping Telegram transport")
        if self.app.running:
            logger.debug("Stopping updater")
            await self.app.updater.stop()
            logger.debug("Stopping application")
            await self.app.stop()
            logger.info("Telegram transport stopped")
        else:
            logger.warning("Attempted to stop non-running application")
        
    def _get_reply_metadata(self, reply_message) -> dict:
        """Helper function to create reply-to metadata."""
        if not reply_message:
            return None
            
        # Determine message type
        message_type = None
        if hasattr(reply_message, 'forum_topic_created'):
            message_type = 'topic_created'
        elif reply_message.text:
            message_type = 'text'
        elif reply_message.photo:
            message_type = 'photo'
        elif reply_message.sticker:
            message_type = 'sticker'
        elif reply_message.video:
            message_type = 'video'
        elif reply_message.voice:
            message_type = 'voice'
        elif reply_message.document:
            message_type = 'document'
        elif reply_message.animation:
            message_type = 'animation'
        elif reply_message.audio:
            message_type = 'audio'
            
        return {
            'message_id': reply_message.message_id,
            'sender_id': reply_message.from_user.id if reply_message.from_user else None,
            'sender_name': (reply_message.from_user.username or reply_message.from_user.first_name) if reply_message.from_user else None,
            'type': message_type,
            'date': reply_message.date.isoformat() if reply_message.date else None
        }

    @trace_operation('transport.telegram')
    async def _handle_message(self, update: Update, context):
        """Log and convert Telegram messages to frames."""
        # Determine all possible message types present
        message_types = []
        if update.message.text:
            message_types.append("text")
        if update.message.photo:
            message_types.append("photo")
        if update.message.sticker:
            message_types.append("sticker")
        if update.message.video:
            message_types.append("video")
        if update.message.voice:
            message_types.append("voice")
        if update.message.document:
            message_types.append("document")
        if update.message.animation:
            message_types.append("animation")
        if update.message.audio:
            message_types.append("audio")
        if update.message.video_note:
            message_types.append("video_note")
        
        chat_type = update.message.chat.type
        is_forum = getattr(update.message.chat, 'is_forum', False)
        thread_id = getattr(update.message, 'message_thread_id', None)
        forum_topic = getattr(update.message, 'forum_topic_created', None)
        
        # For forum messages, if no thread_id is present, this might be in the General topic
        if is_forum and not thread_id:
            thread_id = 1  # General topic in forums always has ID 1
            logger.debug("Forum message without thread_id, assuming General topic (ID: 1)")
        
        # Get topic name if available
        topic_name = None
        if thread_id:
            if thread_id == 1:
                topic_name = "General"
            elif forum_topic:
                topic_name = forum_topic.name
            elif getattr(update.message, 'reply_to_message', None):
                reply = update.message.reply_to_message
                if getattr(reply, 'forum_topic_created', None):
                    topic_name = reply.forum_topic_created.name
        
        logger.debug(f"Received message types: {message_types} in {chat_type} chat")
        
        # Add chat context to the log
        chat_info = f"[{chat_type}"
        if update.message.chat.title:  # For groups/channels
            chat_info += f": {update.message.chat.title}"
            if thread_id:
                thread_info = topic_name or f"Topic {thread_id}"
                chat_info += f" (topic: {thread_info})"
        if update.message.from_user:  # Add sender info if available
            chat_info += f" from {update.message.from_user.username or update.message.from_user.first_name}"
        chat_info += "]"
        
        # Log detailed message information
        logger.debug(
            f"Message details:\n"
            f"- Chat: id={update.message.chat.id}, type={chat_type}\n"
            f"- Is Forum: {is_forum}\n"
            f"- Thread: id={thread_id}\n"
            f"- Is Topic: {getattr(update.message, 'is_topic_message', False)}\n"
            f"- Forum Topic: {forum_topic}\n"
            f"- Reply To: {getattr(update.message, 'reply_to_message', None)}\n"
            f"- Message ID: {update.message.message_id}\n"
            f"- Message Types: {message_types}\n"
            f"- Sender: id={update.message.from_user.id}, "
            f"is_bot={update.message.from_user.is_bot}, "
            f"name={update.message.from_user.first_name}\n"
            f"- Has Caption: {bool(update.message.caption)}\n"
            f"- Caption: {update.message.caption[:50] + '...' if update.message.caption else None}\n"
            f"- File Info: {bool(update.message.document)}\n"
            f"- Sticker Info: {bool(update.message.sticker)}"
        )
        
        # Process supported message types
        if update.message.text:
            logger.info(f"{chat_info} Processing text message: {update.message.text[:50]}...")
            metadata = {
                'chat_id': update.message.chat.id,
                'chat_title': update.message.chat.title or "Private Chat",
                'thread_id': thread_id,
                'thread_name': topic_name,
                'sender_id': update.message.from_user.id,
                'sender_name': update.message.from_user.username or update.message.from_user.first_name
            }
            
            # Add forwarding information if present
            if hasattr(update.message, 'forward_origin') and update.message.forward_origin:
                metadata['forward_origin'] = {
                    'type': update.message.forward_origin.type,
                    'date': update.message.forward_origin.date.isoformat()
                }
                if hasattr(update.message.forward_origin, 'sender_user') and update.message.forward_origin.sender_user:
                    metadata['forward_origin']['sender'] = {
                        'user_id': update.message.forward_origin.sender_user.id,
                        'username': update.message.forward_origin.sender_user.username,
                        'name': update.message.forward_origin.sender_user.first_name
                    }
            
            if hasattr(update.message, 'forward_from') and update.message.forward_from:
                metadata['forwarded_from'] = {
                    'user_id': update.message.forward_from.id,
                    'username': update.message.forward_from.username,
                    'name': update.message.forward_from.first_name
                }
                
            if hasattr(update.message, 'forward_date') and update.message.forward_date:
                metadata['forward_date'] = update.message.forward_date.isoformat()
            
            # Add link preview information if present
            if hasattr(update.message, 'web_page') and update.message.web_page:
                web_page = update.message.web_page
                metadata['web_page'] = {
                    'url': web_page.url,
                    'type': web_page.type,
                    'title': web_page.title,
                    'description': web_page.description,
                    'site_name': web_page.site_name,
                    'has_large_media': bool(web_page.has_large_media),
                    'has_media': bool(web_page.has_media),
                    'display_url': web_page.display_url,
                }
                # Add thumbnail info if present
                if hasattr(web_page, 'thumbnail') and web_page.thumbnail:
                    metadata['web_page']['thumbnail'] = {
                        'width': web_page.thumbnail.width,
                        'height': web_page.thumbnail.height,
                        'file_id': web_page.thumbnail.file_id
                    }
            
            # Add reply-to information if present
            reply_meta = self._get_reply_metadata(update.message.reply_to_message)
            if reply_meta:
                metadata['reply_to'] = reply_meta
            
            frame = TextFrame(
                text=update.message.text,
                metadata=metadata
            )
            logger.debug("Created TextFrame, pushing to pipeline")
            await self.push_frame(frame)
            logger.debug("TextFrame pushed to pipeline")
            
        elif update.message.photo:
            logger.info(f"{chat_info} Processing photo message")
            photo = update.message.photo[-1]  # Get highest quality photo
            logger.debug(f"Photo size: {photo.width}x{photo.height}")
            file = await context.bot.get_file(photo.file_id)
            logger.info(f"PHOTO DEBUG - File path from Telegram: {file.file_path}")
            photo_bytes = await file.download_as_bytearray()
            logger.debug(f"Downloaded photo ({len(photo_bytes)} bytes)")
            
            # Extract format from file path
            format = "jpeg"  # Default if we can't determine
            if file.file_path:
                ext = file.file_path.split('.')[-1].lower()
                logger.info(f"PHOTO DEBUG - Original extension: {ext}")
                if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                    format = ext
                    if format == 'jpg':
                        format = 'jpeg'
                    logger.info(f"PHOTO DEBUG - Using format: {format}")
                else:
                    logger.warning(f"PHOTO DEBUG - Unrecognized extension {ext}, defaulting to jpeg")
            else:
                logger.warning("PHOTO DEBUG - No file path available, defaulting to jpeg")
            
            metadata = {
                'chat_id': update.message.chat.id,
                'chat_title': update.message.chat.title or "Private Chat",
                'thread_id': thread_id,
                'thread_name': topic_name,
                'sender_id': update.message.from_user.id,
                'sender_name': update.message.from_user.username or update.message.from_user.first_name,
                'caption': update.message.caption,
                'original_format': format,
                'file_path': file.file_path,
                'file_id': photo.file_id
            }
            
            # Add reply-to information if present
            reply_meta = self._get_reply_metadata(update.message.reply_to_message)
            if reply_meta:
                metadata['reply_to'] = reply_meta
            
            frame = ImageFrame(
                content=bytes(photo_bytes),
                size=(photo.width, photo.height),
                format=format,
                metadata=metadata
            )
            logger.info(f"PHOTO DEBUG - Created ImageFrame with format={format}, thread_id={thread_id}, topic_name={topic_name}")
            await self.push_frame(frame)
            logger.debug("ImageFrame pushed to pipeline")

        elif update.message.sticker:
            logger.info(f"{chat_info} Processing sticker message")
            sticker = update.message.sticker
            logger.debug(f"Sticker: animated={sticker.is_animated}, video={sticker.is_video}, size={sticker.width}x{sticker.height}")
            file = await context.bot.get_file(sticker.file_id)
            logger.debug("Retrieved file info")
            sticker_bytes = await file.download_as_bytearray()
            logger.debug(f"Downloaded sticker ({len(sticker_bytes)} bytes)")
            
            # Determine format based on sticker type
            if sticker.is_animated:
                format = "tgs"  # Telegram animated sticker format (gzipped Lottie)
                mime_type = "application/x-tgsticker"
            elif sticker.is_video:
                format = "webm"  # Video stickers are WebM
                mime_type = "video/webm"
            else:
                format = "webp"  # Static stickers are WebP
                mime_type = "image/webp"
            
            metadata = {
                'chat_id': update.message.chat.id,
                'chat_title': update.message.chat.title or "Private Chat",
                'thread_id': thread_id,
                'thread_name': topic_name,
                'sender_id': update.message.from_user.id,
                'sender_name': update.message.from_user.username or update.message.from_user.first_name,
                'is_animated': sticker.is_animated,
                'is_video': sticker.is_video,
                'emoji': sticker.emoji,
                'format': format,
                'sticker_set': sticker.set_name,
                'file_unique_id': sticker.file_unique_id
            }
            
            # Add reply-to information if present
            reply_meta = self._get_reply_metadata(update.message.reply_to_message)
            if reply_meta:
                metadata['reply_to'] = reply_meta
            
            frame = StickerFrame(
                content=bytes(sticker_bytes),
                emoji=sticker.emoji,
                set_name=sticker.set_name,
                metadata=metadata
            )
            logger.debug(f"Created StickerFrame (format={format}, set={sticker.set_name}), pushing to pipeline")
            await self.push_frame(frame)
            logger.debug("StickerFrame pushed to pipeline")

        elif update.message.document:
            logger.info(f"{chat_info} Processing document message")
            doc = update.message.document
            logger.debug(f"Document: name={doc.file_name}, type={doc.mime_type}, size={doc.file_size}")
            file = await context.bot.get_file(doc.file_id)
            logger.debug("Retrieved file info")
            doc_bytes = await file.download_as_bytearray()
            logger.debug(f"Downloaded document ({len(doc_bytes)} bytes)")
            metadata = {
                'chat_id': update.message.chat.id,
                'chat_title': update.message.chat.title or "Private Chat",
                'thread_id': thread_id,
                'thread_name': topic_name,
                'sender_id': update.message.from_user.id,
                'sender_name': update.message.from_user.username or update.message.from_user.first_name,
                'file_size': doc.file_size
            }
            
            # Add reply-to information if present
            reply_meta = self._get_reply_metadata(update.message.reply_to_message)
            if reply_meta:
                metadata['reply_to'] = reply_meta
            
            frame = DocumentFrame(
                content=bytes(doc_bytes),
                filename=doc.file_name,
                mime_type=doc.mime_type,
                caption=update.message.caption,
                metadata=metadata
            )
            logger.debug("Created DocumentFrame, pushing to pipeline")
            await self.push_frame(frame)
            logger.debug("DocumentFrame pushed to pipeline")

        elif update.message.video:
            logger.info(f"{chat_info} Processing video message")
            video = update.message.video
            logger.debug(f"Video: name={video.file_name}, type={video.mime_type}, size={video.file_size}, duration={video.duration}s, dimensions={video.width}x{video.height}")
            file = await context.bot.get_file(video.file_id)
            logger.debug("Retrieved file info")
            video_bytes = await file.download_as_bytearray()
            logger.debug(f"Downloaded video ({len(video_bytes)} bytes)")
            
            metadata = {
                'chat_id': update.message.chat.id,
                'chat_title': update.message.chat.title or "Private Chat",
                'thread_id': thread_id,
                'thread_name': topic_name,
                'sender_id': update.message.from_user.id,
                'sender_name': update.message.from_user.username or update.message.from_user.first_name,
                'type': 'documentframe',
                'source': 'telegram',
                'message_id': update.message.message_id,
                'date': update.message.date.isoformat(),
                'file_size': video.file_size,
                'duration': video.duration,
                'width': video.width,
                'height': video.height,
                'has_thumbnail': bool(video.thumbnail),
                'file_id': video.file_id,
                'file_unique_id': video.file_unique_id,
                'mime_type': video.mime_type,
                'original_filename': video.file_name
            }
            
            # Download and store thumbnail if present
            if video.thumbnail:
                thumbnail = video.thumbnail
                thumbnail_file = await context.bot.get_file(thumbnail.file_id)
                thumbnail_bytes = await thumbnail_file.download_as_bytearray()
                logger.debug(f"Downloaded thumbnail ({len(thumbnail_bytes)} bytes)")
                metadata['thumbnail'] = {
                    'width': thumbnail.width,
                    'height': thumbnail.height,
                    'file_id': thumbnail.file_id,
                    'file_unique_id': thumbnail.file_unique_id,
                    'file_size': thumbnail.file_size,
                    'mime_type': 'image/jpeg'
                }
                # Create and push a separate frame for the thumbnail
                thumbnail_frame = DocumentFrame(
                    content=bytes(thumbnail_bytes),
                    filename=f"{video.file_unique_id}_thumb.jpg",
                    mime_type='image/jpeg',
                    metadata={
                        'chat_id': update.message.chat.id,
                        'chat_title': update.message.chat.title or "Private Chat",
                        'thread_id': thread_id,
                        'thread_name': topic_name,
                        'sender_id': update.message.from_user.id,
                        'sender_name': update.message.from_user.username or update.message.from_user.first_name,
                        'type': 'thumbnail',
                        'source': 'telegram',
                        'parent_message_id': update.message.message_id,
                        'width': thumbnail.width,
                        'height': thumbnail.height,
                        'file_id': thumbnail.file_id,
                        'file_unique_id': thumbnail.file_unique_id
                    }
                )
                await self.push_frame(thumbnail_frame)
                logger.debug("Thumbnail DocumentFrame pushed to pipeline")
            
            # Add reply-to information if present
            reply_meta = self._get_reply_metadata(update.message.reply_to_message)
            if reply_meta:
                metadata['reply_to'] = reply_meta
            
            frame = DocumentFrame(
                content=bytes(video_bytes),
                filename=video.file_name,
                mime_type=video.mime_type,
                caption=update.message.caption,
                metadata=metadata
            )
            logger.debug("Created DocumentFrame for video, pushing to pipeline")
            await self.push_frame(frame)
            logger.debug("Video DocumentFrame pushed to pipeline")

        elif update.message.audio or update.message.voice:
            logger.info(f"{chat_info} Processing audio/voice message")
            audio = update.message.audio or update.message.voice
            logger.debug(f"Audio: duration={audio.duration}s, size={getattr(audio, 'file_size', 'unknown')}")
            file = await context.bot.get_file(audio.file_id)
            logger.debug("Retrieved file info")
            audio_bytes = await file.download_as_bytearray()
            logger.debug(f"Downloaded audio ({len(audio_bytes)} bytes)")
            
            # Get file info based on the type
            if update.message.audio:
                # For audio files, use original filename and mime type if available
                original_filename = getattr(audio, 'file_name', None)
                if original_filename:
                    filename = original_filename
                    # Extract extension from original filename
                    ext = original_filename.split('.')[-1].lower()
                else:
                    # Extract extension from file path or default to mp3
                    ext = file.file_path.split('.')[-1].lower() if file.file_path else 'mp3'
                    filename = f"{audio.file_unique_id}.{ext}"
                mime_type = getattr(audio, 'mime_type', 'audio/mpeg')
                logger.debug(f"Audio file: name={filename}, type={mime_type}, ext={ext}")
                
                metadata = {
                    'chat_id': update.message.chat.id,
                    'chat_title': update.message.chat.title or "Private Chat",
                    'thread_id': thread_id,
                    'thread_name': topic_name,
                    'sender_id': update.message.from_user.id,
                    'sender_name': update.message.from_user.username or update.message.from_user.first_name,
                    'duration': audio.duration,
                    'file_size': getattr(audio, 'file_size', len(audio_bytes)),
                    'file_id': audio.file_id,
                    'file_unique_id': audio.file_unique_id,
                    'performer': getattr(audio, 'performer', None),  # Audio file metadata
                    'title': getattr(audio, 'title', None),         # Audio file metadata
                    'original_filename': getattr(audio, 'file_name', None)  # Store original filename
                }
                
                # Add reply-to information if present
                reply_meta = self._get_reply_metadata(update.message.reply_to_message)
                if reply_meta:
                    metadata['reply_to'] = reply_meta
                
                frame = AudioFrame(
                    content=bytes(audio_bytes),
                    duration=audio.duration,
                    mime_type=mime_type,
                    metadata=metadata
                )
                logger.debug("Created AudioFrame, pushing to pipeline")
                await self.push_frame(frame)
                logger.debug("AudioFrame pushed to pipeline")
            else:  # Voice message
                # Voice messages are always Opus encoded in OGG container
                mime_type = 'audio/ogg'
                logger.debug("Voice message: using OGG/Opus format")
                
                metadata = {
                    'chat_id': update.message.chat.id,
                    'chat_title': update.message.chat.title or "Private Chat",
                    'thread_id': thread_id,
                    'thread_name': topic_name,
                    'sender_id': update.message.from_user.id,
                    'sender_name': update.message.from_user.username or update.message.from_user.first_name,
                    'duration': audio.duration,
                    'file_size': getattr(audio, 'file_size', len(audio_bytes)),
                    'file_id': audio.file_id,
                    'file_unique_id': audio.file_unique_id
                }
                
                # Add reply-to information if present
                reply_meta = self._get_reply_metadata(update.message.reply_to_message)
                if reply_meta:
                    metadata['reply_to'] = reply_meta
                
                frame = VoiceFrame(
                    content=bytes(audio_bytes),
                    duration=audio.duration,
                    mime_type=mime_type,
                    metadata=metadata
                )
                logger.debug("Created VoiceFrame, pushing to pipeline")
                await self.push_frame(frame)
                logger.debug("VoiceFrame pushed to pipeline")

        else:
            logger.info(f"{chat_info} Received unsupported message types: {message_types}")
            
    @trace_operation('transport.telegram')
    async def process_frame(self, frame: Frame):
        """Process frames (not used in this transport as it's input-only)."""
        logger.debug(f"Ignoring incoming frame of type {type(frame)}")

    @trace_operation('transport.telegram')
    async def send(self, frame: Frame) -> Optional[Frame]:
        """Send a frame through the transport (not implemented as this is input-only)."""
        logger.debug(f"Send not implemented for frame type {type(frame)}")
        return None

    @trace_operation('transport.telegram')
    async def _handle_command(self, update: Update, context) -> None:
        """Handle bot commands."""
        logger.info(f"Received command: {update.message.text}")
        
        # Extract command and args
        parts = update.message.text.split()
        command = parts[0].lower()
        args = parts[1:]
        
        # Create metadata
        metadata = {
            'chat_id': update.message.chat.id,
            'chat_title': update.message.chat.title or "Private Chat",
            'sender_id': update.message.from_user.id,
            'sender_name': update.message.from_user.username or update.message.from_user.first_name
        }
        
        # Add thread info if present
        thread_id = getattr(update.message, 'message_thread_id', None)
        if thread_id:
            metadata['thread_id'] = thread_id
            if thread_id == 1:
                metadata['thread_name'] = "General"
            elif hasattr(update.message, 'forum_topic_created'):
                metadata['thread_name'] = update.message.forum_topic_created.name
        
        # Create and push command frame
        frame = CommandFrame(command=command, args=args, metadata=metadata)
        logger.debug(f"Created CommandFrame: {command} with args: {args}")
        await self.push_frame(frame)
        logger.debug("CommandFrame pushed to pipeline") 