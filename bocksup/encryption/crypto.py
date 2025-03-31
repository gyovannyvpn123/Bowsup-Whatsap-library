"""
Module for AES encryption and decryption.

This module provides AES-based encryption and decryption utilities
used by the library for securing messages and other data.
"""

import os
import base64
import hashlib
from typing import Union, Optional, Tuple, Dict, Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class AESCipher:
    """
    AES cipher implementation for encryption and decryption.
    
    This class provides methods for AES-CBC encryption and decryption
    with automatic padding and IV handling.
    """
    
    def __init__(self, key: Optional[bytes] = None, block_size: int = AES.block_size):
        """
        Initialize the AES cipher.
        
        Args:
            key: Encryption key (if None, a random key will be generated)
            block_size: AES block size in bytes (default is 16)
        """
        self.key = key if key is not None else os.urandom(32)  # 256-bit key
        self.block_size = block_size
        
    def encrypt(self, data: Union[str, bytes]) -> Dict[str, str]:
        """
        Encrypt data using AES-CBC with random IV.
        
        Args:
            data: Data to encrypt (string or bytes)
            
        Returns:
            Dictionary containing base64-encoded 'iv' and 'ciphertext'
        """
        # Convert string to bytes if necessary
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        # Generate a random IV
        iv = os.urandom(self.block_size)
        
        # Create AES cipher
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # Pad and encrypt the data
        padded_data = pad(data, self.block_size)
        ciphertext = cipher.encrypt(padded_data)
        
        # Return base64 encoded IV and ciphertext
        return {
            'iv': base64.b64encode(iv).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
        }
        
    def decrypt(self, iv: Union[str, bytes], ciphertext: Union[str, bytes]) -> bytes:
        """
        Decrypt AES-CBC encrypted data.
        
        Args:
            iv: Initialization vector (base64 string or bytes)
            ciphertext: Encrypted data (base64 string or bytes)
            
        Returns:
            Decrypted data as bytes
            
        Raises:
            ValueError: If decryption fails
        """
        # Convert base64 strings to bytes if necessary
        if isinstance(iv, str):
            iv = base64.b64decode(iv)
            
        if isinstance(ciphertext, str):
            ciphertext = base64.b64decode(ciphertext)
            
        # Create AES cipher
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # Decrypt and unpad the data
        padded_data = cipher.decrypt(ciphertext)
        
        try:
            return unpad(padded_data, self.block_size)
        except ValueError as e:
            raise ValueError(f"Decryption failed: {str(e)}")
            
    def encrypt_file(self, input_file: str, output_file: str) -> Dict[str, str]:
        """
        Encrypt a file using AES-CBC.
        
        Args:
            input_file: Path to the file to encrypt
            output_file: Path to save the encrypted file
            
        Returns:
            Dictionary containing base64-encoded 'iv'
        """
        # Read the input file
        with open(input_file, 'rb') as f:
            data = f.read()
            
        # Encrypt the data
        encrypted = self.encrypt(data)
        
        # Write the IV and ciphertext to the output file
        with open(output_file, 'wb') as f:
            iv_bytes = base64.b64decode(encrypted['iv'])
            ciphertext_bytes = base64.b64decode(encrypted['ciphertext'])
            f.write(iv_bytes + ciphertext_bytes)
            
        return {'iv': encrypted['iv']}
        
    def decrypt_file(self, input_file: str, output_file: str, iv: Optional[Union[str, bytes]] = None) -> bool:
        """
        Decrypt a file encrypted with AES-CBC.
        
        Args:
            input_file: Path to the encrypted file
            output_file: Path to save the decrypted file
            iv: Initialization vector (if None, it's assumed to be at the beginning of the file)
            
        Returns:
            True if decryption was successful
        """
        # Read the encrypted file
        with open(input_file, 'rb') as f:
            data = f.read()
            
        # If IV is not provided, assume it's at the beginning of the file
        if iv is None:
            iv = data[:self.block_size]
            ciphertext = data[self.block_size:]
        else:
            # Convert base64 string to bytes if necessary
            if isinstance(iv, str):
                iv = base64.b64decode(iv)
                
            ciphertext = data
            
        # Decrypt the data
        try:
            decrypted = self.decrypt(iv, ciphertext)
            
            # Write the decrypted data to the output file
            with open(output_file, 'wb') as f:
                f.write(decrypted)
                
            return True
        except ValueError:
            return False
            
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None, iterations: int = 100000) -> Tuple[bytes, bytes]:
        """
        Derive an encryption key from a password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (if None, a random salt will be generated)
            iterations: Number of iterations for PBKDF2
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
            
        # Use hashlib's pbkdf2_hmac for key derivation
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)
        
        return key, salt