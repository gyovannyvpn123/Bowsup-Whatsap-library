"""
Binary utilities for Bocksup.

This module provides utility functions for handling binary data used in the WhatsApp protocol.
"""

from typing import Union, Dict, Any, List, Optional
import json
import struct
import logging

from ..common.constants import (
    WS_BINARY_PREFIX,
    WS_BINARY_SUFFIX,
    BINARY_TYPE_JSON,
    BINARY_TYPE_BINARY,
    BINARY_TYPE_MESSAGE,
    BINARY_TYPE_HANDSHAKE,
    BINARY_TYPE_PAIRING,
    BINARY_TYPE_CHALLENGE,
    BINARY_TYPE_RESPONSE
)

logger = logging.getLogger(__name__)

def to_bytes(data: Union[str, bytes]) -> bytes:
    """
    Convert various data types to bytes.
    
    Args:
        data: Data to convert
        
    Returns:
        Data converted to bytes
    """
    if isinstance(data, str):
        return data.encode('utf-8')
    return data

def from_bytes(data: bytes) -> str:
    """
    Convert bytes to string.
    
    Args:
        data: Bytes to convert
        
    Returns:
        Decoded string
    """
    return data.decode('utf-8')

def encode_binary_message(message_type: int, data: Union[Dict[str, Any], str, bytes]) -> bytes:
    """
    Encode a message into the WhatsApp binary protocol format.
    
    Args:
        message_type: Type of message (from BINARY_TYPE_* constants)
        data: Message data to encode
        
    Returns:
        Encoded binary message
    """
    # Convert data to appropriate format based on message type
    if isinstance(data, dict):
        # For JSON data
        data = json.dumps(data).encode('utf-8')
    elif isinstance(data, str):
        data = data.encode('utf-8')
    
    # Calculate data length
    data_length = len(data)
    
    # Create header with binary prefix, message type, and data length
    header = WS_BINARY_PREFIX + struct.pack('>BI', message_type, data_length)
    
    # Combine header, data, and binary suffix
    return header + data + WS_BINARY_SUFFIX

def decode_binary_message(binary_data: bytes) -> tuple:
    """
    Decode a binary message from WhatsApp.
    
    Args:
        binary_data: Binary data received from WhatsApp
        
    Returns:
        Tuple containing (message_type, decoded_data)
    """
    try:
        if not binary_data:
            raise ValueError("Empty binary data")
        
        # Check for binary message format
        if not (binary_data.startswith(WS_BINARY_PREFIX) and binary_data.endswith(WS_BINARY_SUFFIX)):
            # This might be a text frame
            if len(binary_data) < 100:
                logger.warning(f"Received non-binary message: {binary_data}")
            else:
                logger.warning(f"Received non-binary message of length {len(binary_data)}")
            
            # Try to decode as UTF-8 string
            try:
                return (None, binary_data.decode('utf-8'))
            except UnicodeDecodeError:
                return (None, binary_data)
        
        # Extract message type and data length from header
        prefix_len = len(WS_BINARY_PREFIX)
        suffix_len = len(WS_BINARY_SUFFIX)
        
        # Header format: 4 bytes prefix + 1 byte message type + 4 bytes data length
        header_len = prefix_len + 5
        
        if len(binary_data) < header_len + suffix_len:
            raise ValueError("Binary data too short")
        
        message_type = binary_data[prefix_len]
        data_length = struct.unpack('>I', binary_data[prefix_len+1:prefix_len+5])[0]
        
        # Extract message data
        data_start = prefix_len + 5
        data_end = data_start + data_length
        
        if data_end + suffix_len > len(binary_data):
            raise ValueError(f"Data length mismatch: expected {data_length}, got {len(binary_data) - data_start - suffix_len}")
        
        data = binary_data[data_start:data_end]
        
        # Try to decode data based on message type
        if message_type == BINARY_TYPE_JSON:
            try:
                decoded_data = json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.warning("Failed to decode JSON data, returning raw bytes")
                decoded_data = data
        else:
            decoded_data = data
        
        return (message_type, decoded_data)
    
    except Exception as e:
        logger.error(f"Error decoding binary message: {str(e)}")
        
        # Return raw data on error
        return (None, binary_data)

def encode_json_message_binary(message: Dict[str, Any]) -> bytes:
    """
    Encode a JSON message into binary format.
    
    Args:
        message: JSON message to encode
        
    Returns:
        Encoded binary message
    """
    return encode_binary_message(BINARY_TYPE_JSON, message)

def encode_handshake_binary(handshake_data: Dict[str, Any]) -> bytes:
    """
    Encode a handshake message into binary format.
    
    Args:
        handshake_data: Handshake data to encode
        
    Returns:
        Encoded binary message
    """
    return encode_binary_message(BINARY_TYPE_HANDSHAKE, handshake_data)

def encode_pairing_request_binary(phone_number: str, method: str = "sms") -> bytes:
    """
    Encode a pairing request message into binary format.
    
    Args:
        phone_number: Phone number to request pairing for
        method: Pairing method, "sms" or "voice"
        
    Returns:
        Encoded binary message
    """
    pairing_data = {
        "messageType": "request_pairing_code",
        "phoneNumber": phone_number,
        "isPrimaryDevice": True,
        "method": method
    }
    
    return encode_binary_message(BINARY_TYPE_PAIRING, pairing_data)

def encode_challenge_response_binary(challenge_response: Dict[str, Any]) -> bytes:
    """
    Encode a challenge response message into binary format.
    
    Args:
        challenge_response: Challenge response data
        
    Returns:
        Encoded binary message
    """
    return encode_binary_message(BINARY_TYPE_RESPONSE, challenge_response)