#!/usr/bin/env python3
"""
Sample application for Bocksup library.

This app demonstrates how to use the main functionality of the Bocksup
library for WhatsApp integration.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

import bocksup

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BocksupDemo")

# WhatsApp credentials
PHONE_NUMBER = os.environ.get("WHATSAPP_PHONE")
PASSWORD = os.environ.get("WHATSAPP_PASSWORD")


async def test_connection(phone_number: Optional[str] = None):
    """
    Test connection to WhatsApp servers.
    
    Args:
        phone_number: Optional phone number to test pairing code functionality
    """
    logger.info("Testing connection to WhatsApp servers...")
    result = await bocksup.test_server_connection(phone_number)
    
    logger.info(f"Connection test results:")
    logger.info(f"Connection established: {'✓' if result.get('connection') else '✗'}")
    logger.info(f"Handshake completed: {'✓' if result.get('handshake') else '✗'}")
    logger.info(f"Authentication challenge received: {'✓' if result.get('challenge') else '✗'}")
    
    if phone_number:
        logger.info(f"Pairing code requested: {'✓' if result.get('pairing_code') else '✗'}")
        
    if result.get('errors'):
        logger.error("Errors encountered:")
        for error in result['errors']:
            logger.error(f"- {error}")
            
    return result


async def create_and_test_client(phone_number: str, password: Optional[str] = None):
    """
    Create a WhatsApp client and test basic functionality.
    
    Args:
        phone_number: Phone number in international format
        password: Optional password or authentication token
    """
    logger.info(f"Creating WhatsApp client for {phone_number}...")
    client = bocksup.create_client(phone_number, password)
    
    logger.info(f"Client created with the following components:")
    logger.info(f"- Authentication module: {client['auth']}")
    logger.info(f"- Protocol stack: {client['stack']}")
    
    # In a complete implementation, we would connect and interact with WhatsApp here
    
    return client


async def main():
    """Main application function."""
    logger.info(f"Bocksup library version: {bocksup.__version__}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "info"
    
    if command == "info":
        logger.info("Bocksup library info:")
        logger.info(f"- Version: {bocksup.__version__}")
        # List the available modules
        modules = [m for m in dir(bocksup) if not m.startswith('__')]
        logger.info(f"- Available modules: {', '.join(modules)}")
        
    elif command == "test":
        phone_number = sys.argv[2] if len(sys.argv) > 2 else PHONE_NUMBER
        if not phone_number:
            logger.error("No phone number provided for testing.")
            logger.error("Use: python sample_app.py test +1234567890")
            return
            
        await test_connection(phone_number)
        
    elif command == "client":
        phone_number = sys.argv[2] if len(sys.argv) > 2 else PHONE_NUMBER
        password = sys.argv[3] if len(sys.argv) > 3 else PASSWORD
        
        if not phone_number:
            logger.error("No phone number provided for client creation.")
            logger.error("Use: python sample_app.py client +1234567890 [password]")
            return
            
        await create_and_test_client(phone_number, password)
        
    else:
        logger.error(f"Unknown command: {command}")
        logger.error("Available commands: info, test, client")
    
    
if __name__ == "__main__":
    asyncio.run(main())