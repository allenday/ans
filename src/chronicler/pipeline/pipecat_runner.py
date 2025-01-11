from typing import List, Type
import asyncio
import logging
import signal
import os
from pathlib import Path

from .frames import Frame
from .pipeline import Pipeline

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_bot(token: str, storage_path: str):
    """Run the Telegram bot with pipeline-based processing."""
    
    # Import components here to avoid circular imports
    from chronicler.transports.telegram_transport import TelegramTransport
    from chronicler.processors.storage_processor import StorageProcessor
    from chronicler.services.git_sync_service import GitSyncService
    from chronicler.commands import CommandProcessor
    from chronicler.commands.handlers import (
        StartCommandHandler,
        ConfigCommandHandler,
        StatusCommandHandler
    )
    
    # Initialize components
    storage_path = Path(storage_path)
    transport = TelegramTransport(token)
    storage = StorageProcessor(storage_path)
    
    # Initialize git sync service if configured
    sync_service = None
    if storage.git_processor:
        sync_interval = int(os.getenv('GIT_SYNC_INTERVAL', '300'))
        sync_service = GitSyncService(
            storage.git_processor,
            sync_interval=sync_interval
        )
        logger.info("Initialized git sync service (interval: %d seconds)", sync_interval)
    
    # Initialize command processor with handlers
    command_processor = CommandProcessor()
    command_processor.register_handler("/start", StartCommandHandler(storage))
    command_processor.register_handler("/config", ConfigCommandHandler(storage))
    command_processor.register_handler("/status", StatusCommandHandler(storage))
    logger.debug("Registered command handlers")
    
    # Create pipeline with command processor
    pipeline = Pipeline([
        transport,
        command_processor,  # Handle commands before storage
        storage
    ])
    logger.debug("Created pipeline with command handling")
    
    # Setup shutdown handler
    loop = asyncio.get_event_loop()
    stop = asyncio.Event()
    
    def signal_handler():
        logger.info("Shutting down...")
        stop.set()
    
    try:
        logger.info("Starting bot...")
        await transport.start()
        
        # Start git sync service if configured
        if sync_service:
            await sync_service.start()
            logger.info("Started git sync service")
        
        # Setup signal handlers after services are started
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        
        await stop.wait()  # Wait until stop signal
    finally:
        # Stop git sync service if running
        if sync_service:
            await sync_service.stop()
            logger.info("Stopped git sync service")
        
        await transport.stop()

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description='Run Chronicler with pipeline processing')
    parser.add_argument('--token', required=True, help='Telegram bot token')
    parser.add_argument('--storage', required=True, help='Storage directory path')
    
    args = parser.parse_args()
    asyncio.run(run_bot(args.token, args.storage))

if __name__ == '__main__':
    main() 