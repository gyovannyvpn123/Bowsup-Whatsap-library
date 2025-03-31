"""
Bocksup - WhatsApp Integration Library

A Python library that replicates yowsup's WhatsApp integration functionality 
with improved stability, error handling, and modern Python compatibility.

This library provides a complete implementation of the WhatsApp protocol,
allowing you to build applications that can send and receive messages,
handle media, participate in group chats, and more.

Version: 0.1.0
License: MIT
"""

__version__ = '0.1.0'
__author__ = 'Bocksup Team'

from bocksup.config.settings import Settings
from bocksup.stack.builder import StackBuilder

# Simple configuration for client code
config = Settings()

# Make key classes available at package level
def create_stack(credentials, encryption_enabled=True):
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
