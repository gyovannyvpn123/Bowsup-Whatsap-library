"""
Cryptographic utilities for WhatsApp protocol.
"""

import logging
import os
import base64
import hashlib
import hmac
import time
from typing import Tuple, Dict, Any, Optional, Union, List

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from bocksup.common.exceptions import EncryptionError

logger = logging.getLogger(__name__)

class Crypto:
    """
    Cryptographic utilities for WhatsApp protocol.
    
    This class provides cryptographic functions used by the WhatsApp protocol,
    including encryption, decryption, and various hashing operations.
    """
    
    @staticmethod
    def encrypt_aes(data: Union[str, bytes], key: Union[str, bytes], iv: Optional[bytes] = None) -> bytes:
        """
        Encrypt data using AES-256-CBC.
        
        Args:
            data: Data to encrypt
            key: Encryption key
            iv: Initialization vector (if None, a random one is generated)
            
        Returns:
            Encrypted data with IV prepended
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Convert data and key to bytes if they're strings
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            if isinstance(key, str):
                key = key.encode('utf-8')
                
            # Ensure key is the right length for AES-256
            if len(key) != 32:  # 256 bits = 32 bytes
                key = hashlib.sha256(key).digest()
                
            # Generate random IV if none provided
            if iv is None:
                iv = os.urandom(AES.block_size)
                
            # Pad data to block size
            padded_data = pad(data, AES.block_size)
            
            # Create cipher and encrypt
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(padded_data)
            
            # Prepend IV to ciphertext
            return iv + encrypted
            
        except Exception as e:
            logger.error(f"AES encryption error: {str(e)}")
            raise EncryptionError(f"AES encryption failed: {str(e)}")
    
    @staticmethod
    def decrypt_aes(data: bytes, key: Union[str, bytes]) -> bytes:
        """
        Decrypt AES-256-CBC encrypted data.
        
        Args:
            data: Encrypted data with IV prepended
            key: Decryption key
            
        Returns:
            Decrypted data
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Convert key to bytes if it's a string
            if isinstance(key, str):
                key = key.encode('utf-8')
                
            # Ensure key is the right length for AES-256
            if len(key) != 32:  # 256 bits = 32 bytes
                key = hashlib.sha256(key).digest()
                
            # Extract IV from the beginning of the data
            iv = data[:AES.block_size]
            ciphertext = data[AES.block_size:]
            
            # Create cipher and decrypt
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_plaintext = cipher.decrypt(ciphertext)
            
            # Unpad the plaintext
            return unpad(padded_plaintext, AES.block_size)
            
        except Exception as e:
            logger.error(f"AES decryption error: {str(e)}")
            raise EncryptionError(f"AES decryption failed: {str(e)}")
    
    @staticmethod
    def hmac_sha256(key: Union[str, bytes], data: Union[str, bytes]) -> bytes:
        """
        Calculate HMAC-SHA256 digest.
        
        Args:
            key: HMAC key
            data: Data to hash
            
        Returns:
            HMAC-SHA256 digest
            
        Raises:
            EncryptionError: If HMAC calculation fails
        """
        try:
            # Convert key and data to bytes if they're strings
            if isinstance(key, str):
                key = key.encode('utf-8')
                
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            # Calculate HMAC
            h = hmac.new(key, data, hashlib.sha256)
            return h.digest()
            
        except Exception as e:
            logger.error(f"HMAC-SHA256 error: {str(e)}")
            raise EncryptionError(f"HMAC-SHA256 failed: {str(e)}")
    
    @staticmethod
    def sha256(data: Union[str, bytes]) -> bytes:
        """
        Calculate SHA-256 hash.
        
        Args:
            data: Data to hash
            
        Returns:
            SHA-256 hash
            
        Raises:
            EncryptionError: If hashing fails
        """
        try:
            # Convert data to bytes if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            # Calculate hash
            h = hashlib.sha256(data)
            return h.digest()
            
        except Exception as e:
            logger.error(f"SHA-256 error: {str(e)}")
            raise EncryptionError(f"SHA-256 failed: {str(e)}")
    
    @staticmethod
    def base64_encode(data: Union[str, bytes]) -> str:
        """
        Encode data as base64.
        
        Args:
            data: Data to encode
            
        Returns:
            Base64-encoded string
            
        Raises:
            EncryptionError: If encoding fails
        """
        try:
            # Convert data to bytes if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            # Encode as base64
            return base64.b64encode(data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Base64 encoding error: {str(e)}")
            raise EncryptionError(f"Base64 encoding failed: {str(e)}")
    
    @staticmethod
    def base64_decode(data: str) -> bytes:
        """
        Decode base64 data.
        
        Args:
            data: Base64-encoded string
            
        Returns:
            Decoded bytes
            
        Raises:
            EncryptionError: If decoding fails
        """
        try:
            # Decode base64
            return base64.b64decode(data)
            
        except Exception as e:
            logger.error(f"Base64 decoding error: {str(e)}")
            raise EncryptionError(f"Base64 decoding failed: {str(e)}")
    
    @staticmethod
    def generate_random_bytes(length: int) -> bytes:
        """
        Generate cryptographically secure random bytes.
        
        Args:
            length: Number of bytes to generate
            
        Returns:
            Random bytes
        """
        return os.urandom(length)
    
    @staticmethod
    def pkcs5_unpad(data: bytes) -> bytes:
        """
        Remove PKCS#5 padding from data.
        
        Args:
            data: Padded data
            
        Returns:
            Unpadded data
            
        Raises:
            EncryptionError: If unpadding fails
        """
        try:
            return unpad(data, AES.block_size)
        except Exception as e:
            logger.error(f"PKCS#5 unpadding error: {str(e)}")
            raise EncryptionError(f"PKCS#5 unpadding failed: {str(e)}")
    
    @staticmethod
    def pkcs5_pad(data: bytes) -> bytes:
        """
        Add PKCS#5 padding to data.
        
        Args:
            data: Data to pad
            
        Returns:
            Padded data
            
        Raises:
            EncryptionError: If padding fails
        """
        try:
            return pad(data, AES.block_size)
        except Exception as e:
            logger.error(f"PKCS#5 padding error: {str(e)}")
            raise EncryptionError(f"PKCS#5 padding failed: {str(e)}")
    
    @staticmethod
    def derive_key(password: str, salt: bytes, iterations: int = 2000) -> bytes:
        """
        Derive a key from a password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation
            iterations: Number of iterations for PBKDF2
            
        Returns:
            Derived key
            
        Raises:
            EncryptionError: If key derivation fails
        """
        try:
            # Convert password to bytes if it's a string
            if isinstance(password, str):
                password = password.encode('utf-8')
                
            # Derive key using PBKDF2
            return hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen=32)
            
        except Exception as e:
            logger.error(f"Key derivation error: {str(e)}")
            raise EncryptionError(f"Key derivation failed: {str(e)}")
