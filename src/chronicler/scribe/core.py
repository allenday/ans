from typing import Dict, Optional
from telegram import Update
from chronicler.storage.interface import StorageAdapter, Message, Topic
from chronicler.storage.config_interface import ConfigStorageAdapter
from chronicler.scribe.interface import (
    ScribeConfig, UserSession, GroupConfig, 
    UserState, MessageConverter, CommandResponse,
    ScribeInterface
)

class Scribe(ScribeInterface):
    """Core scribe functionality"""
    def __init__(self, config: ScribeConfig, storage: StorageAdapter, telegram_bot, config_store: ConfigStorageAdapter):
        self.config = config
        self.storage = storage
        self.bot = telegram_bot
        self.config_store = config_store
        self.sessions: Dict[int, UserSession] = {}
        self.groups: Dict[int, GroupConfig] = {}
        self.is_running = False

    async def start(self) -> None:
        """Initialize the scribe"""
        await self.storage.init_storage()
        await self._load_state()
        self.is_running = True

    async def stop(self) -> None:
        """Stop the scribe"""
        await self._save_state()
        self.is_running = False

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

    async def _load_state(self) -> None:
        """Load persisted state"""
        state = await self.config_store.load()
        
        # Load config
        if "github_token" in state:
            self.config.github_token = state["github_token"]
        if "github_repo" in state:
            self.config.github_repo = state["github_repo"]
            
        # Load sessions
        if "sessions" in state:
            for user_id_str, session_data in state["sessions"].items():
                user_id = int(user_id_str)
                self.sessions[user_id] = UserSession(
                    user_id=user_id,
                    state=UserState[session_data["state"]],
                    context=session_data.get("context", {})
                )
                
        # Load groups
        if "groups" in state:
            for group_id_str, group_data in state["groups"].items():
                group_id = int(group_id_str)
                self.groups[group_id] = GroupConfig(
                    group_id=group_id,
                    topic_id=group_data["topic_id"],
                    enabled=group_data.get("enabled", True),
                    filters=group_data.get("filters", {})
                )

    async def _save_state(self) -> None:
        """Save state to persistent storage"""
        state = {
            # Save config
            "github_token": self.config.github_token,
            "github_repo": self.config.github_repo,
            
            # Save sessions
            "sessions": {
                str(user_id): {
                    "state": session.state.name,
                    "context": session.context
                }
                for user_id, session in self.sessions.items()
            },
            
            # Save groups
            "groups": {
                str(group_id): {
                    "topic_id": group.topic_id,
                    "enabled": group.enabled,
                    "filters": group.filters
                }
                for group_id, group in self.groups.items()
            }
        }
        
        await self.config_store.save(state)

    async def handle_command(self, update: Update) -> CommandResponse:
        """Handle bot commands"""
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

    def get_user_session(self, user_id: int) -> UserSession:
        """Get or create user session"""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id=user_id)
        return self.sessions[user_id]

    def get_group_config(self, group_id: int) -> Optional[GroupConfig]:
        """Get group configuration if it exists"""
        return self.groups.get(group_id)

    async def enable_group(self, group_id: int, topic_id: str) -> None:
        """Enable monitoring for a group"""
        self.groups[group_id] = GroupConfig(
            group_id=group_id,
            topic_id=topic_id,
            enabled=True,
            filters={}
        )
        await self.storage.create_topic(Topic(id=topic_id, name=f"Group {group_id}"))
        await self._save_state()  # Save state after enabling group

    # Command handlers
    async def _handle_start(self, update: Update) -> CommandResponse:
        return CommandResponse(text="Welcome to Chronicler! Use /help to see available commands.")

    async def _handle_help(self, update: Update) -> CommandResponse:
        help_text = """
        Available commands:
        /start - Start the bot
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
        """Handle /status command"""
        user_id = update.message.from_user.id
        session = self.get_user_session(user_id)
        
        status = []
        if self.config.github_token and self.config.github_repo:
            status.append("GitHub: Configured")
        else:
            status.append("GitHub: Not configured")
            
        monitored = len([g for g in self.groups.values() if g.enabled])
        status.append(f"Monitored groups: {monitored}")
        
        return CommandResponse(text="\n".join(status))

    async def _handle_setup(self, update: Update) -> CommandResponse:
        """Handle /setup command"""
        user_id = update.message.from_user.id
        session = self.get_user_session(user_id)
        session.state = UserState.AWAITING_GITHUB_TOKEN
        await self._save_state()  # Save state after updating session
        return CommandResponse(text="Please provide your GitHub token")

    async def _handle_monitor(self, update: Update) -> CommandResponse:
        """Handle /monitor command"""
        if not (self.config.github_token and self.config.github_repo):
            return CommandResponse(text="GitHub integration must be configured first", error=True)
        
        args = update.message.text.split()
        if len(args) != 2:
            return CommandResponse(text="Usage: /monitor <topic_id>", error=True)
            
        topic_id = args[1]
        await self.enable_group(update.message.chat.id, topic_id)
        return CommandResponse(text="Monitoring enabled")

    async def _handle_unmonitor(self, update: Update) -> CommandResponse:
        """Handle /unmonitor command"""
        group_id = update.message.chat.id
        if group_id in self.groups:
            self.groups[group_id].enabled = False
            await self._save_state()  # Save state after disabling monitoring
            return CommandResponse(text="Monitoring disabled")
        return CommandResponse(text="This group is not being monitored", error=True)

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

    async def _handle_sync(self, update: Update) -> CommandResponse:
        """Handle /sync command"""
        if not (self.config.github_token and self.config.github_repo):
            return CommandResponse(text="GitHub integration must be configured first", error=True)
        await self.storage.sync()
        return CommandResponse(text="Changes synced to remote")

    async def _handle_list(self, update: Update) -> CommandResponse:
        """Handle /list command"""
        if not self.groups:
            return CommandResponse(text="No monitored groups")
            
        groups = [f"{gid}: {g.topic_id}" for gid, g in self.groups.items() if g.enabled]
        return CommandResponse(text="Monitored groups:\n" + "\n".join(groups))

    # [Additional command handlers to be implemented] 