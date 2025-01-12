import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, List
from chronicler.processors.git_processor import GitProcessor, GitProcessingError

logger = logging.getLogger(__name__)

class GitSyncService:
    """Service for asynchronously syncing git repository."""
    
    def __init__(
        self,
        git_processor: GitProcessor,
        sync_interval: int = 300,
        max_retries: int = 3,
        retry_delay: int = 60
    ):
        """Initialize GitSyncService.
        
        Args:
            git_processor: GitProcessor instance for git operations
            sync_interval: Seconds between sync attempts (default: 300)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Seconds to wait between retries (default: 60)
        """
        self.git_processor = git_processor
        self.sync_interval = sync_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the sync service."""
        if self._running:
            logger.warning("GitSyncService is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info("Started GitSyncService (interval: %d seconds)", self.sync_interval)
    
    async def stop(self) -> None:
        """Stop the sync service."""
        if not self._running:
            logger.warning("GitSyncService is not running")
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped GitSyncService")
    
    async def commit_immediately(self, path: Union[Path, List[Path]], is_media: bool = False) -> None:
        """Immediately commit a file or list of files locally.
        
        Args:
            path: Single Path or list of Paths to commit
            is_media: Whether the files are media files (affects commit message)
        """
        try:
            # Convert single path to list for uniform handling
            paths = [path] if isinstance(path, Path) else path
            
            # Run git commit in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._commit_files,
                paths,
                is_media
            )
            logger.info("Successfully committed %d files locally", len(paths))
            
        except GitProcessingError as e:
            logger.error("Failed to commit files locally", exc_info=True)
            raise
    
    def _commit_files(self, paths: List[Path], is_media: bool) -> None:
        """Helper method to commit files using the git processor.
        
        Args:
            paths: List of paths to commit
            is_media: Whether the files are media files
        """
        if is_media:
            self.git_processor.commit_media(paths)
        else:
            # For now, treat all non-media as messages
            # We only get one path for messages currently
            self.git_processor.commit_message(paths[0])
    
    async def _sync_loop(self) -> None:
        """Main sync loop."""
        while self._running:
            try:
                await self._sync_with_retry()
            except Exception as e:
                logger.error("Unexpected error in sync loop", exc_info=True)
            
            await asyncio.sleep(self.sync_interval)
    
    async def _sync_with_retry(self) -> None:
        """Attempt to sync with retries on failure."""
        for attempt in range(self.max_retries):
            try:
                # Run git push in executor to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    None, self.git_processor.push_changes
                )
                return
            except GitProcessingError as e:
                if attempt == self.max_retries - 1:
                    logger.error(
                        "Failed to sync after %d attempts", 
                        self.max_retries,
                        exc_info=True
                    )
                    return
                
                logger.warning(
                    "Sync attempt %d/%d failed, retrying in %d seconds",
                    attempt + 1,
                    self.max_retries,
                    self.retry_delay,
                    exc_info=True
                )
                await asyncio.sleep(self.retry_delay) 