from pathlib import Path
from git import Repo
import json
from datetime import datetime
import shutil
from chronicler.logging import get_logger, trace_operation
from enum import Enum, auto
from git.exc import InvalidGitRepositoryError

logger = get_logger(__name__)

class EntityType(Enum):
    """Types of entities that can be stored."""
    USER = auto()
    GROUP = auto()
    SUPERGROUP = auto()
    TOPIC = auto()

class GitStorageAdapter:
    """Git-based storage implementation."""
    
    def __init__(self, base_path: str | Path):
        """Initialize git storage."""
        self.base_path = Path(base_path)
        self.logger = logger.getChild(self.__class__.__name__)
        self.repo = None
        self._init_repo()
        
    def _init_repo(self):
        """Initialize Git repository."""
        try:
            self.repo = Repo(self.base_path)
            # Ensure we're on main branch
            if 'main' not in self.repo.heads:
                self.repo.git.branch("-M", "main")
        except InvalidGitRepositoryError:
            self.repo = Repo.init(self.base_path)
            self.repo.git.branch("-M", "main")  # Ensure we're on main branch
            # Create initial commit if repo is empty
            if not self.repo.head.is_valid():
                # Create .gitkeep to allow committing an empty directory
                (self.base_path / '.gitkeep').touch()
                self.repo.index.add('.gitkeep')
                self.repo.index.commit('Initial commit')
        
    @trace_operation('storage.git')
    def init_storage(self, source: str) -> None:
        """Initialize storage for a source (e.g. telegram, discord)."""
        source_path = self.base_path / source
        if not source_path.exists():
            source_path.mkdir(parents=True)
            
            # Initialize source metadata
            metadata = {
                'source': source,
                'entities': {
                    'users': {},
                    'groups': {},
                    'supergroups': {}
                }
            }
            self._write_source_metadata(source, metadata)
            
            # Create source structure
            (source_path / 'users').mkdir()
            (source_path / 'groups').mkdir()
            (source_path / 'supergroups').mkdir()
            
            # Add and commit new files
            self.repo.index.add([f'{source}/metadata.json'])
            self.repo.index.commit(f'Initialize {source} source')
            
    @trace_operation('storage.git')
    def create_entity(self, source: str, entity_type: EntityType, entity_id: str, metadata: dict) -> None:
        """Create a new entity (user, group, supergroup)."""
        source_meta = self._read_source_metadata(source)
        
        # Determine entity path
        entity_base = {
            EntityType.USER: 'users',
            EntityType.GROUP: 'groups',
            EntityType.SUPERGROUP: 'supergroups'
        }[entity_type]
        
        entity_path = self.base_path / source / entity_base / str(entity_id)
        
        # Create entity structure
        entity_path.mkdir(parents=True, exist_ok=True)
        (entity_path / 'messages.jsonl').touch()
        (entity_path / 'attachments').mkdir(exist_ok=True)
        
        # Update source metadata
        source_meta['entities'][entity_base][str(entity_id)] = {
            **metadata,
            'created_at': datetime.now().isoformat()
        }
        
        self._write_source_metadata(source, source_meta)
        
        # If it's a supergroup, create topics directory
        if entity_type == EntityType.SUPERGROUP:
            (entity_path / 'topics').mkdir(exist_ok=True)
            
        # Commit changes
        entity_rel_path = f'{source}/{entity_base}/{entity_id}'
        self.repo.index.add([
            f'{source}/metadata.json',
            f'{entity_rel_path}/messages.jsonl'
        ])
        self.repo.index.commit(f'Create {entity_type.name.lower()} {entity_id} in {source}')
            
    @trace_operation('storage.git')
    def create_topic(self, source: str, supergroup_id: str, topic_id: str, metadata: dict) -> None:
        """Create a new topic in a supergroup."""
        topic_path = self.base_path / source / 'supergroups' / str(supergroup_id) / 'topics' / str(topic_id)
        topic_path.mkdir(parents=True, exist_ok=True)
        
        # Create topic structure
        (topic_path / 'messages.jsonl').touch()
        (topic_path / 'attachments').mkdir(exist_ok=True)
        
        # Update supergroup metadata
        source_meta = self._read_source_metadata(source)
        supergroup_meta = source_meta['entities']['supergroups'].get(str(supergroup_id), {})
        if 'topics' not in supergroup_meta:
            supergroup_meta['topics'] = {}
        
        supergroup_meta['topics'][str(topic_id)] = {
            **metadata,
            'created_at': datetime.now().isoformat()
        }
        
        source_meta['entities']['supergroups'][str(supergroup_id)] = supergroup_meta
        self._write_source_metadata(source, source_meta)
        
        # Commit changes
        topic_rel_path = f'{source}/supergroups/{supergroup_id}/topics/{topic_id}'
        self.repo.index.add([
            f'{source}/metadata.json',
            f'{topic_rel_path}/messages.jsonl'
        ])
        self.repo.index.commit(f'Create topic {topic_id} in supergroup {supergroup_id}')
            
    @trace_operation('storage.git')
    def save_message(self, source: str, entity_type: EntityType, entity_id: str, message: dict, topic_id: str | None = None) -> None:
        """Save a message to an entity."""
        # Determine message path
        if entity_type == EntityType.SUPERGROUP and topic_id:
            messages_path = self.base_path / source / 'supergroups' / str(entity_id) / 'topics' / str(topic_id) / 'messages.jsonl'
        else:
            entity_base = {
                EntityType.USER: 'users',
                EntityType.GROUP: 'groups',
                EntityType.SUPERGROUP: 'supergroups'
            }[entity_type]
            messages_path = self.base_path / source / entity_base / str(entity_id) / 'messages.jsonl'
        
        # Append message
        with messages_path.open('a') as f:
            json.dump(message, f)
            f.write('\n')
            
        # Commit changes
        rel_path = str(messages_path.relative_to(self.base_path))
        self.repo.index.add([rel_path])
        commit_msg = f'Add message to {entity_type.name.lower()} {entity_id}'
        if topic_id:
            commit_msg += f' topic {topic_id}'
        self.repo.index.commit(commit_msg)
        
    @trace_operation('storage.git')
    def save_attachment(self, source: str, entity_type: EntityType, entity_id: str, file_path: str | Path, attachment_name: str, topic_id: str | None = None) -> None:
        """Save an attachment."""
        # Determine attachment path
        if entity_type == EntityType.SUPERGROUP and topic_id:
            attachments_path = self.base_path / source / 'supergroups' / str(entity_id) / 'topics' / str(topic_id) / 'attachments'
        else:
            entity_base = {
                EntityType.USER: 'users',
                EntityType.GROUP: 'groups',
                EntityType.SUPERGROUP: 'supergroups'
            }[entity_type]
            attachments_path = self.base_path / source / entity_base / str(entity_id) / 'attachments'
        
        # Copy attachment file
        dest_path = attachments_path / attachment_name
        shutil.copy2(file_path, dest_path)
        
        # Commit changes
        rel_path = str(dest_path.relative_to(self.base_path))
        self.repo.index.add([rel_path])
        commit_msg = f'Add attachment {attachment_name} to {entity_type.name.lower()} {entity_id}'
        if topic_id:
            commit_msg += f' topic {topic_id}'
        self.repo.index.commit(commit_msg)
        
    @trace_operation('storage.git')
    def sync(self, source: str) -> None:
        """Sync changes with remote storage."""
        try:
            # Check if there are any remotes by trying to iterate
            if not list(self.repo.remotes):
                raise RuntimeError("No remotes configured")
            origin = self.repo.remotes['origin']
            
            # Set up tracking branch if needed
            if not self.repo.head.tracking_branch():
                self.repo.git.branch("-u", "origin/main", "main")
            
            origin.push()
        except Exception as e:
            logger.error(f"Failed to sync changes: {e}")
            raise RuntimeError(f"Failed to sync changes: {e}")
        
    @trace_operation('storage.git')
    def set_github_config(self, token: str, repo: str) -> None:
        """Configure GitHub remote."""
        try:
            # Delete existing origin remote if it exists
            if 'origin' in self.repo.remotes:
                self.repo.delete_remote('origin')
            # Create new remote using GitPython API
            self.repo.create_remote('origin', f'https://{token}@github.com/{repo}')
        except Exception as e:
            logger.error(f"Failed to configure GitHub remote: {e}")
            raise RuntimeError(f"Failed to configure GitHub remote: {e}")
        
    def _read_source_metadata(self, source: str) -> dict:
        """Read source metadata from file."""
        metadata_file = self.base_path / source / 'metadata.json'
        if metadata_file.exists():
            with metadata_file.open() as f:
                return json.load(f)
        return {
            'source': source,
            'entities': {
                'users': {},
                'groups': {},
                'supergroups': {}
            }
        }
        
    def _write_source_metadata(self, source: str, metadata: dict) -> None:
        """Write source metadata to file."""
        metadata_file = self.base_path / source / 'metadata.json'
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with metadata_file.open('w') as f:
            json.dump(metadata, f) 