"""Pipeline-based bot runner."""
from typing import List, Type
import asyncio
import signal
from pathlib import Path

from chronicler.logging import get_logger
from chronicler.frames.base import Frame
from chronicler.commands.processor import CommandProcessor
from chronicler.handlers.command import StartCommandHandler, ConfigCommandHandler, StatusCommandHandler
from chronicler.transports.telegram_bot_transport import TelegramBotTransport
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.exceptions import TransportAuthenticationError
from .pipeline import Pipeline

logger = get_logger(__name__, component="pipeline.runner")

async def run_bot(token: str, storage_path: str):
    """Run the Telegram bot with pipeline-based processing."""
    
    if not token or not storage_path:
        raise ValueError("Token and storage path are required")
    
    # Initialize components
    storage_path = Path(storage_path)
    transport = TelegramBotTransport(token)
    storage = StorageProcessor(storage_path)
    
    # Initialize command processor with handlers
    command_processor = CommandProcessor()
    command_processor.register_handler(StartCommandHandler(storage), "/start")
    command_processor.register_handler(ConfigCommandHandler(storage), "/config")
    command_processor.register_handler(StatusCommandHandler(storage), "/status")
    logger.debug("Registered command handlers")
    
    # Create pipeline with command processor
    pipeline = Pipeline()
    pipeline.add_processor(transport)
    pipeline.add_processor(command_processor)  # Handle commands before storage
    pipeline.add_processor(storage)
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
        try:
            await transport.authenticate()  # Authenticate before starting
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise TransportAuthenticationError(str(e))
            
        await transport.start()
        await stop.wait()  # Wait until stop signal
    finally:
        await transport.stop()
        await storage.stop()  # Stop storage processor

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