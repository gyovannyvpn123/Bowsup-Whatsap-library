"""
Protocol layer for WhatsApp communication.

This module handles the WhatsApp protocol details, including serialization
and deserialization of messages.
"""

from bocksup.layers.protocol.messages import MessageTypes
from bocksup.layers.protocol.serialization import Serializer

__all__ = ['MessageTypes', 'Serializer']
