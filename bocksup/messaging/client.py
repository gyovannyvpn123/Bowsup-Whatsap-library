"""
Messaging client for WhatsApp.

This module provides a high-level client for sending and receiving
WhatsApp messages.
"""

import time
import uuid
import json
import logging
import asyncio
from typing import Dict, Any, Optional, Union, Callable, List

from ..common.exceptions import (
    ConnectionError,
    AuthenticationError,
    MessageError
)
from ..common.constants import (
    MSG_TYPE_TEXT,
    MSG_TYPE_IMAGE,
    MSG_TYPE_AUDIO,
    MSG_TYPE_VIDEO,
    MSG_TYPE_DOCUMENT,
    MSG_STATUS_PENDING,
    MSG_STATUS_SENT
)
from ..auth.authenticator import Authenticator

logger = logging.getLogger(__name__)

class MessagingClient:
    """
    Client for sending and receiving WhatsApp messages.
    
    This class provides a high-level interface for interacting with WhatsApp,
    including sending messages, receiving notifications, and managing media.
    """
    
    def __init__(self, phone_number: str, password: Optional[str] = None):
        """
        Initialize the messaging client.
        
        Args:
            phone_number: WhatsApp phone number
            password: WhatsApp password or auth token (optional for QR login)
        """
        self.phone_number = phone_number
        self.password = password
        self.authenticator = Authenticator(phone_number, password)
        self.message_handlers = []
        self.presence_handlers = []
        self.receipt_handlers = []
        self.connected = False
        self.authenticated = False
        self._register_default_handlers()
    
    async def connect(self) -> bool:
        """
        Connect and authenticate with WhatsApp.
        
        Returns:
            bool: True if connection and authentication were successful
        """
        try:
            logger.info(f"Conectare pentru numărul de telefon: {self.phone_number}")
            
            # Authenticate with WhatsApp
            authenticated = await self.authenticator.authenticate()
            
            if authenticated:
                logger.info("Autentificare reușită")
                self.authenticated = True
                
                # Save connection reference
                if self.authenticator.connection:
                    self.connection = self.authenticator.connection
                    self.connected = self.connection.is_connected
                
                # Get pairing code if available
                if self.authenticator.pairing_code:
                    logger.info(f"Cod de asociere: {self.authenticator.pairing_code}")
                
                return True
            else:
                logger.error("Autentificare eșuată")
                return False
                
        except Exception as e:
            logger.error(f"Eroare la conectare: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """
        Disconnect from WhatsApp.
        """
        if hasattr(self, 'connection') and self.connection:
            await self.connection.disconnect()
            self.connected = False
            self.authenticated = False
            logger.info("Deconectat de la WhatsApp")
    
    async def send_text_message(self, to: str, text: str) -> Dict:
        """
        Send a text message.
        
        Args:
            to: Recipient's phone number or JID
            text: Message text
            
        Returns:
            Dict containing message ID and status
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        if not self.connected or not hasattr(self, 'connection'):
            raise ConnectionError("Not connected to WhatsApp")
        
        try:
            # Generate message ID
            message_id = f"bocksup_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Create message content
            message = {
                "tag": self.connection.protocol.generate_tag(),
                "type": "message",
                "to": to,
                "id": message_id,
                "content": {
                    "type": MSG_TYPE_TEXT,
                    "text": text
                }
            }
            
            # Send the message
            logger.info(f"Trimitere mesaj către {to}: {text[:30]}...")
            await self.connection.send_message(message)
            
            # Return message info
            return {
                "id": message_id,
                "status": MSG_STATUS_SENT,
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Eroare la trimiterea mesajului: {str(e)}")
            raise MessageError(f"Failed to send message: {str(e)}")
    
    def register_message_handler(self, handler: Callable) -> None:
        """
        Register a handler for incoming messages.
        
        Args:
            handler: Callback function to handle messages
        """
        self.message_handlers.append(handler)
    
    def register_presence_handler(self, handler: Callable) -> None:
        """
        Register a handler for presence updates.
        
        Args:
            handler: Callback function to handle presence updates
        """
        self.presence_handlers.append(handler)
    
    def register_receipt_handler(self, handler: Callable) -> None:
        """
        Register a handler for message receipts.
        
        Args:
            handler: Callback function to handle receipts
        """
        self.receipt_handlers.append(handler)
    
    def _register_default_handlers(self) -> None:
        """
        Register default handlers for various message types.
        """
        # These would be registered with the connection object once it's created
        # during the authentication process
        
        async def message_handler(data):
            """Handle incoming messages."""
            logger.info(f"Mesaj primit: {str(data)[:100]}...")
            
            for handler in self.message_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Eroare în handler de mesaje: {str(e)}")
        
        async def receipt_handler(data):
            """Handle message receipts."""
            logger.info(f"Confirmare primită: {str(data)[:100]}...")
            
            for handler in self.receipt_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Eroare în handler de confirmări: {str(e)}")
        
        async def presence_handler(data):
            """Handle presence updates."""
            logger.info(f"Actualizare prezență: {str(data)[:100]}...")
            
            for handler in self.presence_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Eroare în handler de prezență: {str(e)}")
        
        # These handlers will be connected to the actual connection
        # during the authentication process
        self._default_handlers = {
            "chat_message": message_handler,
            "receipt": receipt_handler,
            "presence": presence_handler
        }