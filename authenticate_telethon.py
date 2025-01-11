import os
from telethon import TelegramClient

# Load environment variables
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')

# Initialize the Telethon client
client = TelegramClient('chronicler', api_id, api_hash)

async def main():
    # Start the client and authenticate
    await client.start(phone_number)
    print("Authentication successful. Session saved.")

# Run the authentication
client.loop.run_until_complete(main()) 