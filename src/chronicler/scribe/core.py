from typing import Dict, Optional, Any
from telegram import Update
import logging
from chronicler.storage.interface import StorageAdapter, Message, Topic, User
from chronicler.storage.config_interface import ConfigStorageAdapter
from chronicler.scribe.interface import (
    ScribeConfig, UserSession, GroupConfig, 
    UserState, MessageConverter, CommandResponse,
    ScribeInterface
)

logger = logging.getLogger(__name__)

class Scribe(ScribeInterface):
    """Core scribe implementation"""
    
    def __init__(self, config: ScribeConfig, storage: StorageAdapter, telegram_bot: Any, config_store: ConfigStorageAdapter):
        logger.info("Initializing Scribe")
        self.config = config
        self.storage = storage
        self.telegram_bot = telegram_bot
        self.config_store = config_store
        self.sessions: Dict[int, UserSession] = {}
        self.groups: Dict[int, GroupConfig] = {}
        self.converter = MessageConverter()
        self.is_running = False
        logger.debug(f"Scribe initialized with config: {config}")
    
    async def start(self) -> None:
        """Start the scribe"""
        logger.info("Starting Scribe")
        await self.storage.init_storage(User(id="test_user", name="Test User"))
        await self._load_state()
        self.is_running = True
        logger.info("Scribe started")
    
    async def stop(self) -> None:
        """Stop the scribe"""
        logger.info("Stopping Scribe")
        await self._save_state()
        self.is_running = False
        logger.info("Scribe stopped")
    
    def get_user_session(self, user_id: int) -> UserSession:
        """Get or create user session"""
        logger.debug(f"Getting session for user {user_id}")
        if user_id not in self.sessions:
            logger.info(f"Creating new session for user {user_id}")
            self.sessions[user_id] = UserSession(user_id=user_id)
        return self.sessions[user_id]
    
    def get_group_config(self, group_id: int) -> Optional[GroupConfig]:
        """Get group configuration if it exists"""
        logger.debug(f"Getting config for group {group_id}")
        config = self.groups.get(group_id)
        if config:
            logger.debug(f"Found config for group {group_id}: {config}")
        else:
            logger.debug(f"No config found for group {group_id}")
        return config
    
    async def enable_group(self, group_id: int, topic_id: str) -> None:
        """Enable monitoring for a group"""
        logger.info(f"Enabling monitoring for group {group_id} with topic {topic_id}")
        self.groups[group_id] = GroupConfig(
            group_id=group_id,
            topic_id=topic_id,
            enabled=True,
            filters={}
        )
        logger.debug(f"Creating topic for group {group_id}")
        await self.storage.create_topic(Topic(id=topic_id, name=f"Group {group_id}"))
        logger.debug("Saving state after enabling group")
        await self._save_state()
    
    async def _save_state(self) -> None:
        """Save state to storage"""
        logger.debug("Saving scribe state")
        try:
            state = {
                'groups': {
                    str(gid): {
                        'group_id': g.group_id,
                        'topic_id': g.topic_id,
                        'enabled': g.enabled,
                        'filters': g.filters
                    }
                    for gid, g in self.groups.items()
                },
                'sessions': {
                    str(uid): {
                        'state': s.state.value,
                        'context': s.context
                    }
                    for uid, s in self.sessions.items()
                }
            }
            await self.config_store.save_state(state)
            logger.info("State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)
            raise
    
    async def _load_state(self) -> None:
        """Load state from storage"""
        logger.debug("Loading scribe state")
        try:
            state = await self.config_store.load_state()
            if not state:
                logger.info("No existing state found")
                return

            # Load group configs
            if 'groups' in state:
                logger.debug(f"Found {len(state['groups'])} groups in state")
                for gid_str, g in state['groups'].items():
                    gid = int(gid_str)
                    self.groups[gid] = GroupConfig(
                        group_id=g['group_id'],
                        topic_id=g['topic_id'],
                        enabled=g['enabled'],
                        filters=g['filters']
                    )
                logger.info(f"Loaded {len(self.groups)} groups from state")

            # Load user sessions
            if 'sessions' in state:
                logger.debug(f"Found {len(state['sessions'])} user sessions in state")
                for uid_str, s in state['sessions'].items():
                    uid = int(uid_str)
                    self.sessions[uid] = UserSession(
                        user_id=uid,
                        state=UserState(s['state']),
                        context=s.get('context', {})
                    )
                logger.info(f"Loaded {len(self.sessions)} user sessions from state")
        except Exception as e:
            logger.error(f"Failed to load state: {e}", exc_info=True)
            raise
    
    # Command handlers
    async def _handle_start(self, update: Update) -> CommandResponse:
        logger.info(f"Handling /start command from user {update.effective_user.id}")
        return CommandResponse(text="Welcome to Chronicler! Use /help to see available commands.")
    
    async def _handle_help(self, update: Update) -> CommandResponse:
        logger.info(f"Handling /help command from user {update.effective_user.id}")
        help_text = """
        Available commands:
        /start - Start the scribe
        /help - Show this help message
        /status - Show current status
        /setup - Configure GitHub integration
        /monitor <topic> - Start monitoring current group
        /unmonitor - Stop monitoring current group
        /filters - Configure message filters
        /sync - Sync changes to GitHub
        /list - List monitored groups
        """
        return CommandResponse(text=help_text)
    
    async def _handle_status(self, update: Update) -> CommandResponse:
        logger.info(f"Handling /status command from user {update.effective_user.id}")
        session = self.get_user_session(update.effective_user.id)
        status_text = f"Current state: {session.state}\n"
        status_text += f"\nGitHub: {'configured' if self.config.github_token and self.config.github_repo else 'not configured'}"
        status_text += f"\nMonitored groups: {len(self.groups)}"
        if update.effective_chat.type != 'private':
            group_id = update.effective_chat.id
            config = self.get_group_config(group_id)
            if config:
                status_text += f"\nGroup monitoring: {'enabled' if config.enabled else 'disabled'}"
                status_text += f"\nTopic: {config.topic_id}"
                if config.filters:
                    status_text += f"\nFilters: {config.filters}"
        return CommandResponse(text=status_text)
    
    async def _handle_monitor(self, update: Update, args: list[str] = None) -> CommandResponse:
        logger.info(f"Handling /monitor command from user {update.effective_user.id}")
        if not self.config.github_token or not self.config.github_repo:
            return CommandResponse(text="GitHub integration must be configured first. Use /setup", error=True)
            
        if not args:
            logger.warning("No topic provided for monitor command")
            return CommandResponse(text="Please provide a topic name: /monitor <topic>", error=True)
        
        topic_name = args[0]
        group_id = update.effective_chat.id
        topic_id = f"group_{group_id}"
        
        logger.debug(f"Enabling monitoring for group {group_id} with topic {topic_name}")
        await self.enable_group(group_id, topic_id)
        return CommandResponse(text=f"Now monitoring this group in topic: {topic_name}")
    
    async def _handle_unmonitor(self, update: Update) -> CommandResponse:
        logger.info(f"Handling /unmonitor command from user {update.effective_user.id}")
        group_id = update.effective_chat.id
        if group_id in self.groups:
            logger.debug(f"Disabling monitoring for group {group_id}")
            del self.groups[group_id]
            await self._save_state()
            return CommandResponse(text="Stopped monitoring this group")
        else:
            logger.debug(f"Group {group_id} was not being monitored")
            return CommandResponse(text="This group is not being monitored", error=True)
    
    async def _handle_sync(self, update: Update) -> CommandResponse:
        logger.info(f"Handling /sync command from user {update.effective_user.id}")
        try:
            await self.storage.sync()
            logger.info("Storage sync completed successfully")
            return CommandResponse(text="Changes synced to remote")
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            return CommandResponse(text=f"Sync failed: {str(e)}", error=True)
    
    async def _handle_list(self, update: Update) -> CommandResponse:
        logger.info(f"Handling /list command from user {update.effective_user.id}")
        if not self.groups:
            return CommandResponse(text="No monitored groups")
        
        groups_text = "Monitored groups:\n"
        for group_id, config in self.groups.items():
            groups_text += f"\nGroup {group_id}:"
            groups_text += f"\n  Topic: {config.topic_id}"
            groups_text += f"\n  Enabled: {config.enabled}"
            if config.filters:
                groups_text += f"\n  Filters: {config.filters}"
        
        logger.debug(f"Found {len(self.groups)} monitored groups")
        return CommandResponse(text=groups_text)

    async def handle_message(self, update: Update) -> CommandResponse:
        """Process incoming messages based on user state"""
        if not update.message or not update.message.from_user:
            return CommandResponse("Invalid message format", error=True)
            
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
        
        # Handle normal message if in a monitored group
        if chat_id in self.groups and self.groups[chat_id].enabled:
            group_config = self.groups[chat_id]
            
            # Apply filters if any
            if group_config.filters:
                # Check media_only filter
                if group_config.filters.get('media_only'):
                    has_media = any([
                        update.message.photo,
                        update.message.video,
                        update.message.document,
                        update.message.sticker,
                        update.message.animation,
                        update.message.voice,
                        update.message.audio
                    ])
                    if not has_media:
                        return CommandResponse("Message filtered - media only")
                
                # Check min_length filter
                min_length = group_config.filters.get('min_length')
                if min_length and len(update.message.text or '') < min_length:
                    return CommandResponse("Message filtered - too short")
                
            # Convert and save message
            storage_msg = await MessageConverter.to_storage_message(update.message)
            await self.storage.save_message(group_config.topic_id, storage_msg)
            return CommandResponse("Message saved")
            
        # Handle user session states
        session = self.sessions.get(user_id)
        if not session:
            return CommandResponse("Message ignored - not in monitored group")
            
        if session.state == UserState.AWAITING_GITHUB_TOKEN:
            self.config.github_token = update.message.text
            session.state = UserState.AWAITING_GITHUB_REPO
            await self._save_state()
            return CommandResponse("Please provide your GitHub repository (format: username/repo)")
            
        elif session.state == UserState.AWAITING_GITHUB_REPO:
            self.config.github_repo = update.message.text
            session.state = UserState.IDLE
            await self._save_state()
            await self.storage.set_github_config(
                token=self.config.github_token,
                repo=self.config.github_repo
            )
            return CommandResponse("GitHub configuration complete!")
            
        elif session.state == UserState.CONFIGURING_GROUP:
            # Handle group configuration
            group_id = session.context.get('configuring_group')
            if not group_id:
                session.state = UserState.IDLE
                return CommandResponse("No group being configured", error=True)
                
            try:
                filters = eval(update.message.text)  # Basic filter parsing
                if not isinstance(filters, dict):
                    raise ValueError("Filters must be a dictionary")
                    
                if group_id in self.groups:
                    self.groups[group_id].filters = filters
                    session.state = UserState.IDLE
                    await self._save_state()
                    return CommandResponse("Group filters updated successfully!")
                else:
                    session.state = UserState.IDLE
                    return CommandResponse("Group not found", error=True)
                    
            except Exception as e:
                session.state = UserState.IDLE
                return CommandResponse(f"Invalid filter format: {str(e)}", error=True)
        
        return CommandResponse("Message ignored - not in monitored group")

    async def handle_command(self, update: Update) -> CommandResponse:
        """Handle scribe commands"""
        command = update.message.text.split()[0].lower()
        user_id = update.message.from_user.id
        
        commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/status': self._handle_status,
            '/setup': self._handle_setup,
            '/monitor': self._handle_monitor,
            '/unmonitor': self._handle_unmonitor,
            '/filters': self._handle_filters,
            '/sync': self._handle_sync,
            '/list': self._handle_list
        }
        
        handler = commands.get(command)
        if not handler:
            return CommandResponse(text="Unknown command", error=True)
            
        return await handler(update)

    async def _handle_setup(self, update: Update) -> CommandResponse:
        """Handle /setup command"""
        user_id = update.message.from_user.id
        session = self.get_user_session(user_id)
        session.state = UserState.AWAITING_GITHUB_TOKEN
        await self._save_state()  # Save state after updating session
        return CommandResponse(text="Please provide your GitHub token")

    async def _handle_filters(self, update: Update) -> CommandResponse:
        """Handle /filters command"""
        group_id = update.message.chat.id
        group = self.get_group_config(group_id)
        if not group:
            return CommandResponse(text="This group is not being monitored", error=True)
            
        args = update.message.text.split()[1:]
        for arg in args:
            key, value = arg.split('=')
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    pass
            group.filters[key] = value
            
        await self._save_state()  # Save state after updating filters
        return CommandResponse(text="Filters updated")

    # [Additional command handlers to be implemented] 