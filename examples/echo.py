#!/usr/bin/env python3
"""
Echo example for Bocksup.

This example demonstrates a simple WhatsApp echo bot using Bocksup.
It connects to WhatsApp, listens for incoming messages, and echoes them back.
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import Dict, Any, Tuple

# Add parent directory to path to import bocksup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bocksup
from bocksup.messaging.messages import TextMessage, MediaMessage
from bocksup.stack.builder import StackBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bocksup.echo')

class EchoBot:
    """Simple WhatsApp echo bot using Bocksup."""
    
    def __init__(self, phone_number: str, password: str):
        """
        Initialize the echo bot.
        
        Args:
            phone_number: WhatsApp phone number
            password: WhatsApp password
        """
        self.phone_number = phone_number
        self.password = password
        self.stack = None
        self.running = False
        
    async def start(self) -> None:
        """Start the echo bot."""
        logger.info("Starting echo bot")
        
        # Create stack builder
        builder = StackBuilder()
        
        # Set message handler
        builder.set_message_handler(self.handle_message)
        
        # Build the stack
        self.stack = builder.build((self.phone_number, self.password))
        
        # Connect to WhatsApp
        if not await self.stack.connect():
            logger.error("Failed to connect to WhatsApp")
            return
            
        # Authenticate
        if not await self.stack.authenticate():
            logger.error("Failed to authenticate with WhatsApp")
            await self.stack.disconnect()
            return
            
        logger.info("Echo bot started and connected to WhatsApp")
        
        # Set running flag
        self.running = True
        
        # Keep the bot running until stopped
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Echo bot task cancelled")
        finally:
            await self.stop()
            
    async def stop(self) -> None:
        """Stop the echo bot."""
        logger.info("Stopping echo bot")
        
        if self.stack:
            await self.stack.disconnect()
            
        self.running = False
        logger.info("Echo bot stopped")
        
    async def handle_message(self, message_data: Dict[str, Any]) -> None:
        """
        Handle incoming WhatsApp messages.
        
        Args:
            message_data: Message data dictionary
        """
        try:
            # Extract message details
            message_type = message_data.get('type')
            
            if message_type == 'text':
                await self.handle_text_message(message_data)
            elif message_type == 'media':
                await self.handle_media_message(message_data)
            else:
                logger.info(f"Received unsupported message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            
    async def handle_text_message(self, message_data: Dict[str, Any]) -> None:
        """
        Handle text messages.
        
        Args:
            message_data: Text message data
        """
        # Extract message details
        from_jid = message_data.get('from')
        body = message_data.get('body', '')
        
        if not from_jid or not body:
            return
            
        logger.info(f"Received text message from {from_jid}: {body}")
        
        # Prepare echo response
        echo_text = f"Echo: {body}"
        
        # Create response message
        response = {
            'type': 'text',
            'to': from_jid,
            'body': echo_text
        }
        
        # Send echo response
        if await self.stack.send_message(response):
            logger.info(f"Sent echo response to {from_jid}")
        else:
            logger.error(f"Failed to send echo response to {from_jid}")
            
    async def handle_media_message(self, message_data: Dict[str, Any]) -> None:
        """
        Handle media messages.
        
        Args:
            message_data: Media message data
        """
        # Extract message details
        from_jid = message_data.get('from')
        media_type = message_data.get('media_type')
        
        if not from_jid:
            return
            
        logger.info(f"Received media message from {from_jid}, type: {media_type}")
        
        # Prepare echo response for media
        response = {
            'type': 'text',
            'to': from_jid,
            'body': f"Received your {media_type} media. Sorry, I can't echo media files yet."
        }
        
        # Send echo response
        if await self.stack.send_message(response):
            logger.info(f"Sent media acknowledgment to {from_jid}")
        else:
            logger.error(f"Failed to send media acknowledgment to {from_jid}")

async def main():
    """Main function to run the echo bot."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Bocksup Echo Bot Example')
    parser.add_argument('phone', help='Phone number (with country code)')
    parser.add_argument('password', help='WhatsApp password')
    args = parser.parse_args()
    
    # Create and start the echo bot
    bot = EchoBot(args.phone, args.password)
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping bot")
    finally:
        await bot.stop()

if __name__ == '__main__':
    asyncio.run(main())
