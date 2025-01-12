from typing import List, Type
import asyncio
import signal
from pathlib import Path

from chronicler.logging import configure_logging, get_logger

from .frames import Frame
from .pipeline import Pipeline

# Set up logging
configure_logging(
    component_context="pipeline.runner",
    log_level="DEBUG"
)
logger = get_logger(__name__)

async def run_bot(token: str, storage_path: str):
    """Run the Telegram bot with pipeline-based processing."""
    
    # Import components here to avoid circular imports
    from chronicler.transports.telegram_transport import TelegramTransport
    from chronicler.processors.storage_processor import StorageProcessor
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
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        logger.info("Starting bot...")
        await transport.start()
        await stop.wait()  # Wait until stop signal
    finally:
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