"""
WebSocket Protocol Manager for WhatsApp communication.

This module handles the WebSocket protocol used in the current WhatsApp Web API,
including message encoding/decoding, binary message parsing, and protocol-specific
handshakes.
"""

import logging
import json
import time
import random
import base64
import struct
from typing import Dict, Any, List, Optional, Union, Tuple, Callable, ByteString

from bocksup.common.exceptions import ProtocolError, ParseError
from bocksup.common.constants import (
    CLIENT_VERSION, WA_SECRET_BUNDLE, PROTOCOL_VERSION,
    TAG_MESSAGE, TAG_RECEIPT, TAG_PRESENCE, TAG_GROUP,
    TAG_NOTIFICATION, TAG_RESPONSE, TAG_ERROR
)
from bocksup.common.utils import (
    generate_message_id, timestamp_now, base64_encode, base64_decode
)

logger = logging.getLogger(__name__)

# Binary message types
BINARY_TAG_MSG = 2
BINARY_TAG_RECEIPT = 1
BINARY_TAG_NOTIFICATION = 4

class WebSocketProtocol:
    """
    Handles the WebSocket protocol for WhatsApp Web.
    
    This class is responsible for formatting messages in the format expected
    by the WhatsApp Web API, and for parsing incoming messages from the API.
    """
    
    def __init__(self):
        """Initialize the WebSocket protocol handler."""
        self._client_id = self._generate_client_id()
        self._client_token = None
        self._server_token = None
        self._message_count = 0
        self._message_tags = {}
        self._last_seen_id = None
    
    def _generate_client_id(self) -> str:
        """
        Generate a client ID for this connection.
        
        Returns:
            A unique client ID string
        """
        # Generate random base64-encoded ID
        random_bytes = bytes(random.getrandbits(8) for _ in range(16))
        return base64.b64encode(random_bytes).decode('utf-8')
    
    def encode_message(self, message: Dict[str, Any]) -> Union[str, bytes]:
        """
        Encode a message for sending over WebSocket.
        
        Args:
            message: The message to encode
            
        Returns:
            The encoded message as string or bytes
            
        Raises:
            ProtocolError: If the message cannot be encoded
        """
        try:
            # Add message tag if not present
            if 'tag' not in message:
                message['tag'] = TAG_MESSAGE
                
            # Add client tag to track responses
            if message.get('tag') == TAG_MESSAGE:
                tag = str(self._message_count)
                self._message_count += 1
                message['_tag'] = tag
                
                # Store in tag map for response matching
                self._message_tags[tag] = message.get('id') or generate_message_id()
            
            # Add timestamps if not present
            if 'timestamp' not in message:
                message['timestamp'] = timestamp_now()
                
            # Convert to JSON
            return json.dumps(message)
            
        except Exception as e:
            logger.error(f"Failed to encode message: {str(e)}")
            raise ProtocolError(f"Message encoding failed: {str(e)}")
    
    def decode_message(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """
        Decode a message received over WebSocket.
        
        Args:
            data: The raw message data
            
        Returns:
            The decoded message as a dictionary
            
        Raises:
            ParseError: If the message cannot be parsed
        """
        try:
            # Handle binary messages
            if isinstance(data, bytes):
                return self._parse_binary_message(data)
                
            # Handle text (JSON) messages
            if isinstance(data, str):
                return json.loads(data)
                
            raise ParseError(f"Unsupported message type: {type(data)}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise ParseError(f"Invalid JSON in message: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to decode message: {str(e)}")
            raise ParseError(f"Message decoding failed: {str(e)}")
    
    def _parse_binary_message(self, data: bytes) -> Dict[str, Any]:
        """
        Parse a binary message from WhatsApp.
        
        Args:
            data: Binary message data
            
        Returns:
            Parsed message as dictionary
            
        Raises:
            ParseError: If the binary message cannot be parsed
        """
        try:
            if len(data) < 3:
                raise ParseError("Binary message too short")
                
            # First byte is message type
            msg_type = data[0]
            
            # Handle different binary message types
            if msg_type == BINARY_TAG_MSG:
                return self._parse_binary_chat_message(data[1:])
            elif msg_type == BINARY_TAG_RECEIPT:
                return self._parse_binary_receipt(data[1:])
            elif msg_type == BINARY_TAG_NOTIFICATION:
                return self._parse_binary_notification(data[1:])
            else:
                # Try to parse as JSON for unknown types (some messages are JSON with binary prefix)
                try:
                    json_str = data[1:].decode('utf-8')
                    return json.loads(json_str)
                except:
                    logger.warning(f"Unknown binary message type: {msg_type}")
                    return {'type': 'unknown', 'binary_type': msg_type, 'data': base64_encode(data)}
                    
        except Exception as e:
            logger.error(f"Binary message parse error: {str(e)}")
            raise ParseError(f"Failed to parse binary message: {str(e)}")
    
    def _parse_binary_chat_message(self, data: bytes) -> Dict[str, Any]:
        """
        Parse a binary chat message.
        
        Args:
            data: Binary message data (without type byte)
            
        Returns:
            Parsed chat message
        """
        # This would contain the complete implementation for parsing binary chat messages
        # For now, we'll return a placeholder
        return {
            'type': TAG_MESSAGE,
            'binary': True,
            'data': base64_encode(data),
            '_needs_decryption': True
        }
    
    def _parse_binary_receipt(self, data: bytes) -> Dict[str, Any]:
        """
        Parse a binary receipt message.
        
        Args:
            data: Binary receipt data (without type byte)
            
        Returns:
            Parsed receipt message
        """
        # This would contain the implementation for parsing binary receipts
        return {
            'type': TAG_RECEIPT,
            'binary': True,
            'data': base64_encode(data)
        }
    
    def _parse_binary_notification(self, data: bytes) -> Dict[str, Any]:
        """
        Parse a binary notification.
        
        Args:
            data: Binary notification data (without type byte)
            
        Returns:
            Parsed notification message
        """
        # This would contain the implementation for parsing binary notifications
        return {
            'type': TAG_NOTIFICATION,
            'binary': True,
            'data': base64_encode(data)
        }
    
    def create_handshake_message(self) -> str:
        """
        Create the initial handshake message for connecting to WhatsApp Web.
        
        Returns:
            Handshake message as JSON string
        """
        handshake = {
            "clientToken": self._client_token or self._client_id,
            "clientVersion": CLIENT_VERSION,
            "connectType": "WIFI_UNKNOWN",
            "connectReason": "USER_ACTIVATED",
            "pushName": "Bocksup",  # Can be customized
            "device": {
                "build": {
                    "name": f"Bocksup {PROTOCOL_VERSION}"
                },
                "os": {
                    "version": "10",
                    "name": "Windows",
                    "build": "10.0.19042"
                }
            }
        }
        
        return json.dumps(handshake)
    
    def create_login_message(self, phone_number: str, password: str) -> Dict[str, Any]:
        """
        Create authentication message for WhatsApp Web.
        
        Args:
            phone_number: WhatsApp phone number
            password: WhatsApp password
            
        Returns:
            Authentication message dictionary
        """
        # The actual WhatsApp Web login requires QR code scanning,
        # but for compatibility with yowsup-style auth, we'll define this method
        auth_msg = {
            'tag': 'auth',
            'phone': phone_number,
            'password': password,
            'client_id': self._client_id,
            'client_token': self._client_token or '',
            'secret_bundle': WA_SECRET_BUNDLE,
            'protocol_version': PROTOCOL_VERSION
        }
        
        return auth_msg
    
    def get_client_id(self) -> str:
        """
        Get the client ID for this connection.
        
        Returns:
            Client ID string
        """
        return self._client_id
    
    def set_tokens(self, client_token: str, server_token: str) -> None:
        """
        Set authentication tokens.
        
        Args:
            client_token: Client auth token
            server_token: Server auth token
        """
        self._client_token = client_token
        self._server_token = server_token
    
    def create_presence_message(self, presence_type: str) -> Dict[str, Any]:
        """
        Create a presence update message.
        
        Args:
            presence_type: Type of presence (available, unavailable, typing, etc.)
            
        Returns:
            Presence message dictionary
        """
        presence_msg = {
            'tag': TAG_PRESENCE,
            'type': presence_type,
            'id': generate_message_id(),
            'timestamp': timestamp_now()
        }
        
        return presence_msg
    
    def create_read_receipt(self, message_id: str, jid: str) -> Dict[str, Any]:
        """
        Create a read receipt.
        
        Args:
            message_id: ID of the message that was read
            jid: JID of the sender
            
        Returns:
            Read receipt message dictionary
        """
        receipt = {
            'tag': TAG_RECEIPT,
            'type': 'read',
            'to': jid,
            'id': message_id,
            'timestamp': timestamp_now()
        }
        
        return receipt