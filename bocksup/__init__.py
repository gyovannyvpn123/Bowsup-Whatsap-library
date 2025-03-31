"""
Bocksup - WhatsApp Integration Library

A Python library that replicates yowsup's WhatsApp integration functionality 
with improved stability, error handling, and modern Python compatibility.

This library provides a complete implementation of the WhatsApp protocol,
allowing you to build applications that can send and receive messages,
handle media, participate in group chats, and more.

Version: 0.2.0
License: MIT
"""

__version__ = '0.2.0'
__author__ = 'Bocksup Team'

import os
import time
import hashlib
import random
import base64
import re
import json
import logging
from typing import Any, Dict, List, Optional, Union, Tuple

# Import public interfaces from core modules
from bocksup.config.settings import Settings
from bocksup.stack.builder import StackBuilder
from bocksup.auth.authenticator import Authenticator
from bocksup.layers.protocol.websocket_protocol import WebSocketProtocol
from bocksup.layers.protocol.serialization import Serializer
from bocksup.layers.network.connection import WhatsAppConnection
from bocksup.common.exceptions import (
    AuthenticationError, 
    ConnectionError, 
    ParseError, 
    ProtocolError,
    MessageError
)

# Import messaging
from bocksup.messaging.client import MessagingClient, create_client

# Setup core modules
from bocksup.messaging import messages
from bocksup.encryption import crypto, signal_protocol

# Simplified interfaces
# Simple configuration for client code
config = Settings()

# Public functions to make the library more user-friendly
def generate_random_id() -> str:
    """Generate a random ID suitable for message IDs."""
    return f"{int(time.time())}_{random.randint(1000, 9999)}"

def timestamp_now() -> int:
    """Get current timestamp in seconds."""
    return int(time.time())

def format_phone_number(phone: str) -> str:
    """Format a phone number for WhatsApp use."""
    # Remove any non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    return digits_only

def phone_to_jid(phone: str) -> str:
    """
    Convert a phone number to a JID (Jabber ID) used by WhatsApp.
    
    Args:
        phone: Phone number to convert
        
    Returns:
        JID for the phone number
    """
    formatted_phone = format_phone_number(phone)
    return f"{formatted_phone}@s.whatsapp.net"

# Make key classes available at package level
def create_stack(credentials: Tuple[str, str], encryption_enabled: bool = True):
    """
    Create a protocol stack with the provided credentials
    
    Args:
        credentials (tuple): A tuple of (phone_number, password)
        encryption_enabled (bool): Whether to enable end-to-end encryption
        
    Returns:
        A configured protocol stack ready to connect
    """
    builder = StackBuilder()
    return builder.build(credentials, encryption_enabled)

# Simplified function for testing server connection
async def test_server_connection(phone_number: Optional[str] = None) -> Dict:
    """
    Test connection to WhatsApp servers.
    
    This function attempts to establish a connection with WhatsApp servers
    and perform an initial handshake. If a phone number is provided, it will
    also attempt to request a pairing code.
    
    Args:
        phone_number: Optional phone number for pairing code testing
        
    Returns:
        Dict containing test results with the following keys:
        - connection: bool - whether the connection succeeded
        - handshake: bool - whether the initial handshake succeeded
        - challenge: bool - whether an authentication challenge was received
        - pairing_code: bool - whether a pairing code was requested (only with phone_number)
        - messages: list - messages exchanged with the server
        - errors: list - errors encountered
    """
    from bocksup.test_server_connection import test_server_connection as tsc
    return await tsc(phone_number)

# Importul pentru create_client este acum gestionat direct din bocksup.messaging.client
