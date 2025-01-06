from typing import List, Type
import asyncio
import logging
import signal
from pathlib import Path

from .frames import Frame
from .pipeline import Pipeline
from chronicler.transports.telegram_transport import TelegramTransport
from chronicler.processors.storage_processor import StorageProcessor

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_bot(token: str, storage_path: str):
    """Run the Telegram bot with pipeline-based processing."""
    
    # Initialize components
    transport = TelegramTransport(token)
    storage = StorageProcessor(Path(storage_path))
    
    # Create pipeline
    pipeline = Pipeline([transport, storage])
    
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