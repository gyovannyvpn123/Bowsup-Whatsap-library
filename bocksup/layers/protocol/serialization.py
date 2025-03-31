"""
Message serialization and deserialization for WhatsApp protocol.

This module handles the conversion between Python objects and the binary
formats used in WhatsApp messaging protocol.
"""

import json
import struct
import zlib
import base64
import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, ByteString

from bocksup.common.exceptions import ParseError
from bocksup.common.utils import to_bytes, from_bytes

logger = logging.getLogger(__name__)

class Serializer:
    """
    Main serializer class for WhatsApp protocol messages.
    
    This class provides a unified interface for serializing and deserializing
    messages in the WhatsApp protocol, supporting both binary and text-based
    formats used for different types of messages.
    """
    
    def __init__(self, use_encryption: bool = True, use_compression: bool = True):
        """
        Initialize the serializer.
        
        Args:
            use_encryption: Whether to encrypt messages by default
            use_compression: Whether to compress messages by default
        """
        self.use_encryption = use_encryption
        self.use_compression = use_compression
        self.binary_encoder = BinaryEncoder()
        self.binary_decoder = BinaryDecoder()
        self.ws_serializer = WebSocketMessageSerializer()
        
    def serialize_message(self, message: Dict[str, Any]) -> bytes:
        """
        Serialize a message dictionary to binary format.
        
        Args:
            message: Message dictionary to serialize
            
        Returns:
            Serialized binary message
        """
        return BinaryEncoder.encode_message(
            message, 
            encrypt=self.use_encryption,
            compress=self.use_compression
        )
        
    def deserialize_message(self, data: Union[bytes, str]) -> Dict[str, Any]:
        """
        Deserialize a binary or text message.
        
        Args:
            data: Binary or text message data
            
        Returns:
            Deserialized message dictionary
            
        Raises:
            ParseError: If the message cannot be deserialized
        """
        return self.ws_serializer.deserialize_message(data)
        
    def serialize_handshake(self, client_id: str, client_version: str) -> str:
        """
        Create a handshake message for establishing connection.
        
        Args:
            client_id: Client identifier
            client_version: Client version string
            
        Returns:
            Serialized handshake message
        """
        return self.ws_serializer.serialize_handshake(client_id, client_version)
        
    def serialize_text_message(self, 
                              message: str, 
                              recipient: str, 
                              message_id: Optional[str] = None) -> bytes:
        """
        Serialize a text message for sending.
        
        Args:
            message: Text message content
            recipient: Recipient's JID
            message_id: Optional message ID
            
        Returns:
            Serialized binary message
        """
        msg_dict = self.ws_serializer.serialize_text_message(message, recipient, message_id)
        return self.serialize_message(msg_dict)
        
    def serialize_ack(self, 
                     message_id: str, 
                     recipient: str, 
                     ack_type: str) -> bytes:
        """
        Serialize an acknowledgment message.
        
        Args:
            message_id: Message ID being acknowledged
            recipient: Recipient's JID
            ack_type: Type of acknowledgment
            
        Returns:
            Serialized binary message
        """
        msg_dict = self.ws_serializer.serialize_ack(message_id, recipient, ack_type)
        return self.serialize_message(msg_dict)
        
    def serialize_presence(self, 
                          presence_type: str, 
                          to: Optional[str] = None) -> bytes:
        """
        Serialize a presence update message.
        
        Args:
            presence_type: Type of presence update
            to: Optional recipient JID
            
        Returns:
            Serialized binary message
        """
        msg_dict = self.ws_serializer.serialize_presence(presence_type, to)
        return self.serialize_message(msg_dict)
        
    def serialize_pairing_code_request(self, 
                                     phone_number: str, 
                                     device_id: str) -> str:
        """
        Create a request for a pairing code.
        
        Args:
            phone_number: Phone number in international format
            device_id: Unique device identifier
            
        Returns:
            Serialized pairing code request
        """
        pairing_request = {
            "messageTag": f"pairing_{int(time.time())}",
            "type": "admin",
            "command": "request_code",
            "method": "sms",
            "phone": phone_number,
            "device": device_id,
            "mcc": "000",
            "mnc": "000"
        }
        
        return json.dumps(pairing_request)

# Protocol constants
WA_MESSAGE_HEADER_SIZE = 3
WA_MESSAGE_FLAG_COMPRESSED = 0x02
WA_MESSAGE_FLAG_ENCRYPTED = 0x01

class BinaryEncoder:
    """Encoder for binary WhatsApp protocol messages."""
    
    @staticmethod
    def encode_message(message: Dict[str, Any], encrypt: bool = False, compress: bool = True) -> bytes:
        """
        Encode a message dictionary to binary format.
        
        Args:
            message: The message dictionary to encode
            encrypt: Whether to encrypt the message
            compress: Whether to compress the message
            
        Returns:
            The encoded binary message
        """
        # Convert to JSON string
        json_data = json.dumps(message)
        binary_data = json_data.encode('utf-8')
        
        # Apply compression if requested
        flags = 0
        if compress and len(binary_data) > 200:  # Only compress larger messages
            binary_data = zlib.compress(binary_data)
            flags |= WA_MESSAGE_FLAG_COMPRESSED
            
        # Apply encryption if requested (in real implementation this would use E2E encryption)
        if encrypt:
            binary_data = BinaryEncoder._encrypt_data(binary_data)
            flags |= WA_MESSAGE_FLAG_ENCRYPTED
            
        # Create header (3 bytes: 1 for flags, 2 for length)
        length = len(binary_data)
        if length > 65535:
            raise ValueError("Message too large to encode")
            
        header = struct.pack("!BH", flags, length)
        
        # Combine header and data
        return header + binary_data
        
    @staticmethod
    def _encrypt_data(data: bytes) -> bytes:
        """
        Encrypt binary data (placeholder implementation).
        
        In a real implementation, this would use proper E2E encryption.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        # This is a placeholder - in a real implementation this would use proper encryption
        return data  # For now, return unmodified


class BinaryDecoder:
    """Decoder for binary WhatsApp protocol messages."""
    
    @staticmethod
    def decode_message(data: bytes) -> Dict[str, Any]:
        """
        Decode a binary message to a dictionary.
        
        Args:
            data: The binary message data
            
        Returns:
            The decoded message dictionary
            
        Raises:
            ParseError: If the message cannot be decoded
        """
        if len(data) < WA_MESSAGE_HEADER_SIZE:
            raise ParseError("Message too short to decode")
            
        try:
            # Extract header
            flags, length = struct.unpack("!BH", data[:WA_MESSAGE_HEADER_SIZE])
            
            # Extract message body
            message_data = data[WA_MESSAGE_HEADER_SIZE:]
            if len(message_data) < length:
                raise ParseError(f"Message truncated, expected {length} bytes, got {len(message_data)}")
                
            # Decrypt if necessary
            if flags & WA_MESSAGE_FLAG_ENCRYPTED:
                message_data = BinaryDecoder._decrypt_data(message_data)
                
            # Decompress if necessary
            if flags & WA_MESSAGE_FLAG_COMPRESSED:
                message_data = zlib.decompress(message_data)
                
            # Parse JSON
            message_json = message_data.decode('utf-8')
            return json.loads(message_json)
            
        except (struct.error, zlib.error, UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ParseError(f"Failed to decode message: {str(e)}")
            
    @staticmethod
    def _decrypt_data(data: bytes) -> bytes:
        """
        Decrypt binary data (placeholder implementation).
        
        In a real implementation, this would use proper E2E decryption.
        
        Args:
            data: Data to decrypt
            
        Returns:
            Decrypted data
        """
        # This is a placeholder - in a real implementation this would use proper decryption
        return data  # For now, return unmodified


class WebSocketMessageSerializer:
    """Serializer for WhatsApp WebSocket protocol messages."""
    
    @staticmethod
    def serialize_handshake(client_id: str, client_version: str) -> str:
        """
        Create a handshake message for WebSocket connection.
        
        Args:
            client_id: Client identifier
            client_version: Client version string
            
        Returns:
            JSON string with handshake message
        """
        handshake = {
            "messageTag": f"handshake_{int(time.time())}",
            "clientToken": client_id,
            "protocolVersion": "0.4",
            "connectType": "PHONE_CONNECTING",
            "clientPayload": {
                "connectReason": "USER_ACTIVATED",
                "connectType": "WIFI_UNKNOWN",
                "userAgent": {
                    "platform": "android",
                    "appVersion": client_version,
                    "mcc": "000",
                    "mnc": "000",
                    "osVersion": "10",
                    "manufacturer": "Bocksup",
                    "device": "Python",
                    "osBuildNumber": "bocksup_0.1.0"
                }
            }
        }
        
        return json.dumps(handshake)
        
    @staticmethod
    def serialize_binary_message(data: bytes) -> str:
        """
        Serialize binary data to a WebSocket message format.
        
        Args:
            data: Binary data to serialize
            
        Returns:
            A string that can be sent over WebSocket
        """
        # Convert binary data to base64 for WebSocket text frames
        return base64.b64encode(data).decode('utf-8')
        
    @staticmethod
    def serialize_text_message(
        message: str, 
        recipient: str, 
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a text message in the format expected by WhatsApp.
        
        Args:
            message: The text message content
            recipient: The recipient's JID
            message_id: Optional message ID
            
        Returns:
            Message dictionary ready to be encoded
        """
        if not message_id:
            message_id = f"MID_{int(time.time())}_{hash(message) % 10000}"
            
        return {
            "tag": message_id,
            "type": "message",
            "recipient": recipient,
            "content": {
                "type": "text",
                "body": message
            },
            "timestamp": int(time.time())
        }
        
    @staticmethod
    def serialize_ack(message_id: str, recipient: str, message_type: str) -> Dict[str, Any]:
        """
        Create an acknowledgment message.
        
        Args:
            message_id: The ID of the message being acknowledged
            recipient: The recipient's JID
            message_type: The type of acknowledgment
                          (e.g., "read", "received", "played")
            
        Returns:
            Ack message dictionary ready to be encoded
        """
        return {
            "tag": f"ACK_{message_id}",
            "type": "ack",
            "recipient": recipient,
            "content": {
                "type": message_type,
                "id": message_id
            },
            "timestamp": int(time.time())
        }
        
    @staticmethod
    def serialize_presence(presence_type: str, to: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a presence update message.
        
        Args:
            presence_type: Type of presence (e.g., "available", "unavailable")
            to: Optional recipient JID
            
        Returns:
            Presence message dictionary ready to be encoded
        """
        presence = {
            "tag": f"PRESENCE_{int(time.time())}",
            "type": "presence",
            "content": {
                "type": presence_type,
                "timestamp": int(time.time())
            }
        }
        
        if to:
            presence["recipient"] = to
            
        return presence
        
    @staticmethod
    def deserialize_message(message_data: Union[str, bytes]) -> Dict[str, Any]:
        """
        Deserialize a message received over WebSocket.
        
        Args:
            message_data: The received message data
            
        Returns:
            Parsed message dictionary
            
        Raises:
            ParseError: If the message cannot be parsed
        """
        try:
            # Handle binary data
            if isinstance(message_data, bytes):
                return BinaryDecoder.decode_message(message_data)
                
            # Handle text data (might be JSON or base64)
            if isinstance(message_data, str):
                # Try parsing as JSON
                try:
                    return json.loads(message_data)
                except json.JSONDecodeError:
                    # Try decoding as base64
                    try:
                        binary_data = base64.b64decode(message_data)
                        return BinaryDecoder.decode_message(binary_data)
                    except Exception as e:
                        raise ParseError(f"Could not decode base64 data: {str(e)}")
                        
        except Exception as e:
            raise ParseError(f"Failed to deserialize message: {str(e)}")
            
        # This should not be reached
        raise ParseError("Unknown message format")