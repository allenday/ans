from pathlib import Path
from git import Repo
import yaml
import frontmatter
from datetime import datetime
import uuid

class GitStorage:
    def __init__(self, base_path: Path, user_id: str):
        self.base_path = Path(base_path)
        self.user_id = user_id
        self.repo_path = self.base_path / f"{user_id}_journal"
        self._repo = None

    def init_user_repo(self) -> None:
        """Initialize a new git repository for the user with basic structure"""
        # Create base directories
        self.repo_path.mkdir(parents=True, exist_ok=True)
        topics_dir = self.repo_path / "topics"
        topics_dir.mkdir(exist_ok=True)

        # Initialize metadata file
        metadata_path = self.repo_path / "metadata.yaml"
        if not metadata_path.exists():
            with open(metadata_path, 'w') as f:
                yaml.dump({
                    'user_id': self.user_id,
                    'topics': {}
                }, f)

        # Initialize git repo if not already done
        if not (self.repo_path / ".git").exists():
            self._repo = Repo.init(self.repo_path, initial_branch='main')
            # Initial commit with basic structure
            self._repo.index.add(['topics', 'metadata.yaml'])
            self._repo.index.commit("Initial repository structure")

    def create_topic(self, topic_id: str, topic_name: str) -> None:
        """Create a new topic directory with basic structure"""
        topic_path = self.repo_path / "topics" / topic_id
        topic_path.mkdir(parents=True, exist_ok=True)
        
        # Create messages file and media directory
        (topic_path / "messages.md").touch()
        (topic_path / "media").mkdir(exist_ok=True)

        # Update metadata
        metadata_path = self.repo_path / "metadata.yaml"
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        
        metadata['topics'][topic_id] = {
            'name': topic_name,
            'created_at': datetime.utcnow().isoformat()
        }
        
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)

        # Commit changes
        if not self._repo:
            self._repo = Repo(self.repo_path)
        self._repo.index.add([f'topics/{topic_id}', 'metadata.yaml'])
        self._repo.index.commit(f"Created topic: {topic_name}")

    def record_message(self, topic_id: str, message: dict) -> None:
        """Record a message in the specified topic"""
        messages_file = self.repo_path / "topics" / topic_id / "messages.md"
        
        # Create message with frontmatter
        msg = frontmatter.Post(
            message['text'],
            timestamp=message['timestamp'],
            sender=message['sender'],
            type='message',
            message_id=f"msg_{uuid.uuid4().hex[:8]}"
        )
        
        # Convert to string format manually
        frontmatter_str = f"""---
timestamp: {message['timestamp']}
sender: {message['sender']}
type: message
message_id: {msg.metadata['message_id']}
---

{message['text']}"""

        # Append message to file
        with open(messages_file, 'a') as f:
            f.write('\n\n')  # Ensure separation between messages
            f.write(frontmatter_str)

        # Commit changes
        if not self._repo:
            self._repo = Repo(self.repo_path)
        self._repo.index.add([f'topics/{topic_id}/messages.md'])
        
        # Get topic name from metadata
        metadata_path = self.repo_path / "metadata.yaml"
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        topic_name = metadata['topics'][topic_id]['name']
        
        self._repo.index.commit(f"Added message to topic: {topic_name}")
