"""
Telegram Data Scraper
Extracts messages and media from Ethiopian medical business Telegram channels.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger

from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from telethon.errors import FloodWaitError, ChannelPrivateError

from config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    TELEGRAM_CHANNELS,
    TELEGRAM_MESSAGES_PATH,
    IMAGES_PATH,
    LOGS_PATH,
    validate_config
)

# Configure logging
logger.add(
    LOGS_PATH / "scraper_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)


class TelegramScraper:
    """Scraper for extracting data from Telegram channels."""
    
    def __init__(self):
        """Initialize the Telegram scraper."""
        validate_config()
        self.client = TelegramClient(
            'medical_scraper_session',
            TELEGRAM_API_ID,
            TELEGRAM_API_HASH
        )
        self.scraped_log = LOGS_PATH / 'scraped_channels.json'
        self.load_scraped_log()
    
    def load_scraped_log(self):
        """Load the log of previously scraped channels and dates."""
        if self.scraped_log.exists():
            with open(self.scraped_log, 'r') as f:
                self.scraped_data = json.load(f)
        else:
            self.scraped_data = {}
    
    def save_scraped_log(self):
        """Save the log of scraped channels and dates."""
        with open(self.scraped_log, 'w') as f:
            json.dump(self.scraped_data, f, indent=2)
    
    def mark_as_scraped(self, channel_name: str, date: str):
        """Mark a channel/date combination as scraped."""
        if channel_name not in self.scraped_data:
            self.scraped_data[channel_name] = []
        if date not in self.scraped_data[channel_name]:
            self.scraped_data[channel_name].append(date)
        self.save_scraped_log()
    
    async def download_image(self, message, channel_name: str) -> Optional[str]:
        """
        Download image from a message if it contains media.
        
        Args:
            message: Telegram message object
            channel_name: Name of the channel
            
        Returns:
            Path to the downloaded image or None
        """
        if not message.media or not isinstance(message.media, MessageMediaPhoto):
            return None
        
        try:
            # Create channel-specific directory
            channel_image_dir = IMAGES_PATH / channel_name
            channel_image_dir.mkdir(parents=True, exist_ok=True)
            
            # Download image
            image_filename = f"{message.id}.jpg"
            image_path = channel_image_dir / image_filename
            
            await self.client.download_media(message.media, file=str(image_path))
            
            logger.info(f"Downloaded image: {image_path}")
            return str(image_path.relative_to(IMAGES_PATH.parent))
        
        except Exception as e:
            logger.error(f"Error downloading image from message {message.id}: {e}")
            return None
    
    async def scrape_channel(
        self,
        channel_name: str,
        days_back: int = 30,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape messages from a specific Telegram channel.
        
        Args:
            channel_name: Username or ID of the channel
            days_back: Number of days to scrape backwards from today
            limit: Maximum number of messages to scrape (None for all)
            
        Returns:
            List of message dictionaries
        """
        logger.info(f"Starting to scrape channel: {channel_name}")
        messages_data = []
        
        try:
            # Get the channel entity
            channel = await self.client.get_entity(channel_name)
            channel_title = getattr(channel, 'title', channel_name)
            
            # Calculate the date threshold
            date_threshold = datetime.now() - timedelta(days=days_back)
            
            # Iterate through messages
            message_count = 0
            async for message in self.client.iter_messages(
                channel,
                limit=limit,
                offset_date=datetime.now()
            ):
                # Stop if we've gone beyond the date threshold
                if message.date < date_threshold:
                    break
                
                # Extract message data
                message_dict = {
                    'message_id': message.id,
                    'channel_name': channel_title,
                    'channel_username': channel_name,
                    'message_date': message.date.isoformat(),
                    'message_text': message.text or '',
                    'has_media': message.media is not None,
                    'image_path': None,
                    'views': message.views or 0,
                    'forwards': message.forwards or 0,
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Download image if present
                if message.media:
                    image_path = await self.download_image(message, channel_name)
                    message_dict['image_path'] = image_path
                
                messages_data.append(message_dict)
                message_count += 1
                
                # Log progress every 100 messages
                if message_count % 100 == 0:
                    logger.info(f"Scraped {message_count} messages from {channel_name}")
            
            logger.info(f"Completed scraping {channel_name}: {len(messages_data)} messages")
            return messages_data
        
        except ChannelPrivateError:
            logger.error(f"Channel {channel_name} is private or doesn't exist")
            return []
        
        except FloodWaitError as e:
            logger.warning(f"Rate limit hit. Need to wait {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return await self.scrape_channel(channel_name, days_back, limit)
        
        except Exception as e:
            logger.error(f"Error scraping channel {channel_name}: {e}")
            return []
    
    def save_messages(self, messages: List[Dict], channel_name: str):
        """
        Save scraped messages to JSON files organized by date and channel.
        
        Args:
            messages: List of message dictionaries
            channel_name: Name of the channel
        """
        if not messages:
            logger.warning(f"No messages to save for {channel_name}")
            return
        
        # Group messages by date
        messages_by_date = {}
        for message in messages:
            date_str = message['message_date'][:10]  # YYYY-MM-DD
            if date_str not in messages_by_date:
                messages_by_date[date_str] = []
            messages_by_date[date_str].append(message)
        
        # Save each date's messages
        for date_str, date_messages in messages_by_date.items():
            # Create date directory
            date_dir = TELEGRAM_MESSAGES_PATH / date_str
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON file
            output_file = date_dir / f"{channel_name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(date_messages, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(date_messages)} messages to {output_file}")
            
            # Mark as scraped
            self.mark_as_scraped(channel_name, date_str)
    
    async def scrape_all_channels(self, days_back: int = 30, limit: Optional[int] = None):
        """
        Scrape all configured Telegram channels.
        
        Args:
            days_back: Number of days to scrape backwards
            limit: Maximum messages per channel (None for all)
        """
        logger.info(f"Starting to scrape {len(TELEGRAM_CHANNELS)} channels")
        
        await self.client.start(phone=TELEGRAM_PHONE)
        
        for channel_name in TELEGRAM_CHANNELS:
            try:
                messages = await self.scrape_channel(channel_name, days_back, limit)
                self.save_messages(messages, channel_name)
                
                # Be nice to the API - add a small delay between channels
                await asyncio.sleep(2)
            
            except Exception as e:
                logger.error(f"Failed to scrape {channel_name}: {e}")
                continue
        
        logger.info("Completed scraping all channels")
    
    async def run(self, days_back: int = 30, limit: Optional[int] = None):
        """
        Main entry point for the scraper.
        
        Args:
            days_back: Number of days to scrape backwards
            limit: Maximum messages per channel
        """
        async with self.client:
            await self.scrape_all_channels(days_back, limit)


async def main():
    """Main function to run the scraper."""
    scraper = TelegramScraper()
    
    # Scrape last 30 days, no message limit
    # For testing, you can set limit=100
    await scraper.run(days_back=30, limit=None)


if __name__ == '__main__':
    logger.info("Starting Telegram scraper")
    asyncio.run(main())
    logger.info("Scraper completed")
