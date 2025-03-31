"""
Serialization for WhatsApp protocol messages.
"""

import json
import logging
import struct
import zlib
from typing import Dict, Any, Optional, Union, Tuple, List

from construct import Struct, Byte, Int16ub, Int32ub, Bytes, Prefixed
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from bocksup.common.exceptions import ProtocolError
from bocksup.layers.protocol.messages import (
    ProtocolMessage, 
    create_message_from_dict
)

logger = logging.getLogger(__name__)

class Serializer:
    """
    Handles serialization and deserialization of WhatsApp protocol messages.
    
    This class converts between ProtocolMessage objects and binary or JSON
    representations that are sent over the network.
    """
    
    # Protocol header format using construct library
    HEADER = Struct(
        "version" / Byte,
        "flags" / Byte,
        "message_type" / Byte,
        "length" / Int32ub,
    )
    
    # Protocol versions
    VERSION_BINARY = 1
    VERSION_JSON = 2
    VERSION_PROTOBUF = 3
    
    # Flags
    FLAG_NONE = 0
    FLAG_COMPRESSED = 1
    FLAG_ENCRYPTED = 2
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize the serializer.
        
        Args:
            encryption_key: Optional encryption key for encrypted messages
        """
        self.encryption_key = encryption_key
        
    def serialize(self, 
                  message: Union[ProtocolMessage, Dict[str, Any]], 
                  compress: bool = False, 
                  encrypt: bool = False) -> bytes:
        """
        Serialize a message to bytes.
        
        Args:
            message: Message to serialize
            compress: Whether to compress the message
            encrypt: Whether to encrypt the message
            
        Returns:
            Serialized message as bytes
            
        Raises:
            ProtocolError: If serialization fails
        """
        try:
            # Convert to dictionary if it's a ProtocolMessage
            if isinstance(message, ProtocolMessage):
                message_dict = message.to_dict()
            else:
                message_dict = message
                
            # Convert to JSON
            message_data = json.dumps(message_dict).encode('utf-8')
            
            # Apply compression if requested
            flags = self.FLAG_NONE
            if compress:
                message_data = zlib.compress(message_data)
                flags |= self.FLAG_COMPRESSED
                
            # Apply encryption if requested
            if encrypt:
                if not self.encryption_key:
                    raise ProtocolError("Encryption key not set")
                    
                message_data = self._encrypt_data(message_data)
                flags |= self.FLAG_ENCRYPTED
                
            # Create header
            header = self.HEADER.build({
                "version": self.VERSION_JSON,
                "flags": flags,
                "message_type": 0,  # Not used for JSON, all info is in the JSON data
                "length": len(message_data)
            })
            
            # Combine header and message data
            return header + message_data
            
        except Exception as e:
            logger.error(f"Error serializing message: {str(e)}")
            raise ProtocolError(f"Serialization error: {str(e)}")
            
    def deserialize(self, data: bytes) -> Tuple[ProtocolMessage, bytes]:
        """
        Deserialize bytes to a message.
        
        Args:
            data: Bytes to deserialize
            
        Returns:
            Tuple of (deserialized message, remaining data)
            
        Raises:
            ProtocolError: If deserialization fails
        """
        try:
            # Need at least the header to process
            if len(data) < self.HEADER.sizeof():
                return None, data
                
            # Parse header
            header = self.HEADER.parse(data[:self.HEADER.sizeof()])
            
            # Get message length from header
            message_length = header.length
            
            # Check if we have the complete message
            total_length = self.HEADER.sizeof() + message_length
            if len(data) < total_length:
                return None, data
                
            # Extract message data
            message_data = data[self.HEADER.sizeof():total_length]
            
            # Decrypt if needed
            if header.flags & self.FLAG_ENCRYPTED:
                if not self.encryption_key:
                    raise ProtocolError("Message is encrypted but no encryption key is set")
                    
                message_data = self._decrypt_data(message_data)
                
            # Decompress if needed
            if header.flags & self.FLAG_COMPRESSED:
                message_data = zlib.decompress(message_data)
                
            # Parse based on version
            if header.version == self.VERSION_JSON:
                # Parse JSON data
                message_dict = json.loads(message_data.decode('utf-8'))
                
                # Create appropriate message object
                message = create_message_from_dict(message_dict)
                
            elif header.version == self.VERSION_BINARY:
                # Binary format not implemented yet
                raise ProtocolError("Binary format not supported yet")
                
            elif header.version == self.VERSION_PROTOBUF:
                # Protobuf format not implemented yet
                raise ProtocolError("Protobuf format not supported yet")
                
            else:
                raise ProtocolError(f"Unknown protocol version: {header.version}")
                
            # Return the parsed message and any remaining data
            return message, data[total_length:]
            
        except Exception as e:
            logger.error(f"Error deserializing message: {str(e)}")
            raise ProtocolError(f"Deserialization error: {str(e)}")
            
    def _encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data using AES.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
            
        Raises:
            ProtocolError: If encryption fails
        """
        try:
            # Ensure data is padded correctly for AES
            padded_data = pad(data, AES.block_size)
            
            # Generate random IV
            from Crypto.Random import get_random_bytes
            iv = get_random_bytes(AES.block_size)
            
            # Create cipher and encrypt
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Prepend IV to encrypted data
            return iv + encrypted_data
            
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise ProtocolError(f"Encryption error: {str(e)}")
            
    def _decrypt_data(self, data: bytes) -> bytes:
        """
        Decrypt data using AES.
        
        Args:
            data: Data to decrypt
            
        Returns:
            Decrypted data
            
        Raises:
            ProtocolError: If decryption fails
        """
        try:
            # Extract IV from beginning of data
            iv = data[:AES.block_size]
            encrypted_data = data[AES.block_size:]
            
            # Create cipher and decrypt
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise ProtocolError(f"Decryption error: {str(e)}")
            
    def set_encryption_key(self, key: bytes) -> None:
        """
        Set the encryption key.
        
        Args:
            key: Encryption key
        """
        self.encryption_key = key
