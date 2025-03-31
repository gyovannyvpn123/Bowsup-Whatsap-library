"""
Axolotl layer for end-to-end encryption.
"""

import logging
import os
import json
import base64
from typing import Dict, Any, Optional, List, Tuple, Union

from bocksup.common.exceptions import EncryptionError
from bocksup.layers.interface.layer import Layer

logger = logging.getLogger(__name__)

class AxolotlLayer(Layer):
    """
    Implements the Signal Protocol (formerly Axolotl) for end-to-end encryption.
    
    This layer handles the encryption and decryption of messages using the
    Signal Protocol, managing key exchanges and session state.
    """
    
    def __init__(self, store_path: str = './keys'):
        """
        Initialize the Axolotl layer.
        
        Args:
            store_path: Path to store encryption keys and session state
        """
        super().__init__("AxolotlLayer")
        self.store_path = store_path
        self.identity_key_pair = None
        self.registration_id = None
        self.sessions = {}
        self.pre_keys = {}
        self.signed_pre_key = None
        
        # Ensure key store directory exists
        os.makedirs(store_path, exist_ok=True)
        
    async def on_start(self) -> None:
        """
        Initialize the layer when it is started.
        """
        # Load keys and sessions
        await self._load_identity()
        await self._load_sessions()
        
        # Generate keys if not already present
        if not self.identity_key_pair:
            await self._generate_identity()
            
        if not self.signed_pre_key:
            await self._generate_signed_pre_key()
            
        if len(self.pre_keys) < 20:
            await self._generate_pre_keys(100)
            
    async def on_stop(self) -> None:
        """
        Clean up when the layer is stopped.
        """
        # Save current state
        await self._save_identity()
        await self._save_sessions()
        
    async def receive_from_upper(self, data: Dict[str, Any]) -> None:
        """
        Process data coming from upper layer - encrypt before sending down.
        
        Args:
            data: Data from upper layer
        """
        try:
            # Check if this message needs encryption
            if data.get('encrypt', False):
                recipient = data.get('to')
                if not recipient:
                    raise EncryptionError("No recipient specified for encrypted message")
                    
                # Encrypt the message body
                encrypted_data = await self._encrypt_message(recipient, data)
                
                # Set the flag to indicate this message is encrypted
                encrypted_data['encrypted'] = True
                
                # Remove the original 'encrypt' flag
                if 'encrypt' in encrypted_data:
                    del encrypted_data['encrypt']
                    
                # Send down the encrypted message
                await self.send_to_lower(encrypted_data)
            else:
                # No encryption needed, pass through
                await self.send_to_lower(data)
                
        except Exception as e:
            logger.error(f"Error processing outgoing message: {str(e)}")
            self.trigger_event('error', {
                'layer': self.name,
                'error': str(e),
                'message': data
            })
            
    async def receive_from_lower(self, data: Dict[str, Any]) -> None:
        """
        Process data coming from lower layer - decrypt before sending up.
        
        Args:
            data: Data from lower layer
        """
        try:
            # Check if this message is encrypted
            if data.get('encrypted', False):
                sender = data.get('from')
                if not sender:
                    raise EncryptionError("No sender specified for encrypted message")
                    
                # Decrypt the message
                decrypted_data = await self._decrypt_message(sender, data)
                
                # Remove the encryption flag
                if 'encrypted' in decrypted_data:
                    del decrypted_data['encrypted']
                    
                # Send up the decrypted message
                await self.send_to_upper(decrypted_data)
            else:
                # Not encrypted, pass through
                await self.send_to_upper(data)
                
        except Exception as e:
            logger.error(f"Error processing incoming message: {str(e)}")
            self.trigger_event('error', {
                'layer': self.name,
                'error': str(e),
                'message': data
            })
            
    async def _encrypt_message(self, recipient: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt a message for a recipient.
        
        Args:
            recipient: Recipient JID
            data: Message data to encrypt
            
        Returns:
            Encrypted message data
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # For this example, we're using a placeholder encryption implementation
            # In a real implementation, this would use the Signal Protocol
            
            # Clone the data to avoid modifying the original
            encrypted = data.copy()
            
            # Check if we have a session with this recipient
            if recipient not in self.sessions:
                # No session, we'd need to perform a key exchange first
                # This is a simplified version, real implementation would be more complex
                await self._establish_session(recipient)
                
            # Get the session for this recipient
            session = self.sessions[recipient]
            
            # Ensure message body is a string
            if 'body' in encrypted and encrypted['body'] is not None:
                if not isinstance(encrypted['body'], str):
                    encrypted['body'] = str(encrypted['body'])
                    
                # Encrypt the message body
                # This is a placeholder - real implementation would use the Signal Protocol
                encrypted_body = self._dummy_encrypt(encrypted['body'], session['key'])
                
                # Replace the original body with the encrypted one
                encrypted['body'] = base64.b64encode(encrypted_body).decode('utf-8')
                encrypted['enc_type'] = 'axolotl'
                
            return encrypted
            
        except Exception as e:
            logger.error(f"Error encrypting message: {str(e)}")
            raise EncryptionError(f"Encryption failed: {str(e)}")
            
    async def _decrypt_message(self, sender: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt a message from a sender.
        
        Args:
            sender: Sender JID
            data: Encrypted message data
            
        Returns:
            Decrypted message data
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Clone the data to avoid modifying the original
            decrypted = data.copy()
            
            # Check encryption type
            enc_type = data.get('enc_type')
            if enc_type != 'axolotl':
                raise EncryptionError(f"Unsupported encryption type: {enc_type}")
                
            # Check if we have a session with this sender
            if sender not in self.sessions:
                # No session, handle key exchange first
                # In a real implementation, this would extract key exchange data from the message
                await self._establish_session(sender)
                
            # Get the session for this sender
            session = self.sessions[sender]
            
            # Decrypt the message body
            if 'body' in decrypted and decrypted['body'] is not None:
                # Decode the base64 encoded encrypted body
                encrypted_body = base64.b64decode(decrypted['body'])
                
                # Decrypt the body
                # This is a placeholder - real implementation would use the Signal Protocol
                decrypted_body = self._dummy_decrypt(encrypted_body, session['key'])
                
                # Replace the encrypted body with the decrypted one
                decrypted['body'] = decrypted_body
                
                # Remove encryption metadata
                if 'enc_type' in decrypted:
                    del decrypted['enc_type']
                    
            return decrypted
            
        except Exception as e:
            logger.error(f"Error decrypting message: {str(e)}")
            raise EncryptionError(f"Decryption failed: {str(e)}")
            
    async def _establish_session(self, jid: str) -> None:
        """
        Establish an encryption session with a contact.
        
        Args:
            jid: Contact JID
            
        Raises:
            EncryptionError: If session establishment fails
        """
        try:
            # This is a placeholder for session establishment
            # In a real implementation, this would perform a key exchange using the Signal Protocol
            
            # Generate a simple session key for demonstration
            import os
            session_key = os.urandom(32)
            
            # Store the session
            self.sessions[jid] = {
                'jid': jid,
                'key': session_key,
                'created': int(os.time() * 1000)
            }
            
            # Save sessions to disk
            await self._save_sessions()
            
            logger.info(f"Established encryption session with {jid}")
            
        except Exception as e:
            logger.error(f"Error establishing session: {str(e)}")
            raise EncryptionError(f"Session establishment failed: {str(e)}")
            
    async def _generate_identity(self) -> None:
        """
        Generate identity keys.
        
        Raises:
            EncryptionError: If key generation fails
        """
        try:
            # This is a placeholder for identity key generation
            # In a real implementation, this would generate a real Signal Protocol identity key pair
            
            import os
            import random
            
            # Generate a dummy identity key pair
            private_key = os.urandom(32)
            public_key = os.urandom(32)
            
            self.identity_key_pair = {
                'private': base64.b64encode(private_key).decode('utf-8'),
                'public': base64.b64encode(public_key).decode('utf-8')
            }
            
            # Generate a registration ID
            self.registration_id = random.randint(1, 16380)
            
            # Save the identity
            await self._save_identity()
            
            logger.info("Generated new identity keys")
            
        except Exception as e:
            logger.error(f"Error generating identity: {str(e)}")
            raise EncryptionError(f"Identity generation failed: {str(e)}")
            
    async def _generate_signed_pre_key(self) -> None:
        """
        Generate a signed pre-key.
        
        Raises:
            EncryptionError: If key generation fails
        """
        try:
            # This is a placeholder for signed pre-key generation
            # In a real implementation, this would generate a real Signal Protocol signed pre-key
            
            import os
            import random
            
            # Generate a dummy signed pre-key
            private_key = os.urandom(32)
            public_key = os.urandom(32)
            signature = os.urandom(64)
            
            self.signed_pre_key = {
                'id': random.randint(1, 16380),
                'private': base64.b64encode(private_key).decode('utf-8'),
                'public': base64.b64encode(public_key).decode('utf-8'),
                'signature': base64.b64encode(signature).decode('utf-8'),
                'created': int(os.time() * 1000)
            }
            
            # Save the identity (includes signed pre-key)
            await self._save_identity()
            
            logger.info("Generated new signed pre-key")
            
        except Exception as e:
            logger.error(f"Error generating signed pre-key: {str(e)}")
            raise EncryptionError(f"Signed pre-key generation failed: {str(e)}")
            
    async def _generate_pre_keys(self, count: int) -> None:
        """
        Generate pre-keys.
        
        Args:
            count: Number of pre-keys to generate
            
        Raises:
            EncryptionError: If key generation fails
        """
        try:
            # This is a placeholder for pre-key generation
            # In a real implementation, this would generate real Signal Protocol pre-keys
            
            import os
            import random
            
            # Find the next pre-key ID
            next_id = 1
            if self.pre_keys:
                next_id = max(int(id) for id in self.pre_keys.keys()) + 1
                
            # Generate dummy pre-keys
            for i in range(count):
                key_id = str(next_id + i)
                private_key = os.urandom(32)
                public_key = os.urandom(32)
                
                self.pre_keys[key_id] = {
                    'id': key_id,
                    'private': base64.b64encode(private_key).decode('utf-8'),
                    'public': base64.b64encode(public_key).decode('utf-8')
                }
                
            # Save the pre-keys
            await self._save_pre_keys()
            
            logger.info(f"Generated {count} new pre-keys")
            
        except Exception as e:
            logger.error(f"Error generating pre-keys: {str(e)}")
            raise EncryptionError(f"Pre-key generation failed: {str(e)}")
            
    async def _load_identity(self) -> None:
        """
        Load identity keys from storage.
        """
        try:
            identity_path = os.path.join(self.store_path, 'identity.json')
            
            if os.path.exists(identity_path):
                with open(identity_path, 'r') as f:
                    data = json.load(f)
                    
                    self.identity_key_pair = data.get('identity_key_pair')
                    self.registration_id = data.get('registration_id')
                    self.signed_pre_key = data.get('signed_pre_key')
                    
                    logger.info("Loaded identity keys from storage")
                    
        except Exception as e:
            logger.error(f"Error loading identity: {str(e)}")
            
    async def _save_identity(self) -> None:
        """
        Save identity keys to storage.
        """
        try:
            identity_path = os.path.join(self.store_path, 'identity.json')
            
            data = {
                'identity_key_pair': self.identity_key_pair,
                'registration_id': self.registration_id,
                'signed_pre_key': self.signed_pre_key
            }
            
            with open(identity_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Saved identity keys to storage")
            
        except Exception as e:
            logger.error(f"Error saving identity: {str(e)}")
            
    async def _load_pre_keys(self) -> None:
        """
        Load pre-keys from storage.
        """
        try:
            pre_keys_path = os.path.join(self.store_path, 'pre_keys.json')
            
            if os.path.exists(pre_keys_path):
                with open(pre_keys_path, 'r') as f:
                    self.pre_keys = json.load(f)
                    
                    logger.info(f"Loaded {len(self.pre_keys)} pre-keys from storage")
                    
        except Exception as e:
            logger.error(f"Error loading pre-keys: {str(e)}")
            
    async def _save_pre_keys(self) -> None:
        """
        Save pre-keys to storage.
        """
        try:
            pre_keys_path = os.path.join(self.store_path, 'pre_keys.json')
            
            with open(pre_keys_path, 'w') as f:
                json.dump(self.pre_keys, f, indent=2)
                
            logger.info(f"Saved {len(self.pre_keys)} pre-keys to storage")
            
        except Exception as e:
            logger.error(f"Error saving pre-keys: {str(e)}")
            
    async def _load_sessions(self) -> None:
        """
        Load sessions from storage.
        """
        try:
            sessions_path = os.path.join(self.store_path, 'sessions.json')
            
            if os.path.exists(sessions_path):
                with open(sessions_path, 'r') as f:
                    self.sessions = json.load(f)
                    
                    logger.info(f"Loaded {len(self.sessions)} sessions from storage")
                    
        except Exception as e:
            logger.error(f"Error loading sessions: {str(e)}")
            
    async def _save_sessions(self) -> None:
        """
        Save sessions to storage.
        """
        try:
            sessions_path = os.path.join(self.store_path, 'sessions.json')
            
            with open(sessions_path, 'w') as f:
                json.dump(self.sessions, f, indent=2)
                
            logger.info(f"Saved {len(self.sessions)} sessions to storage")
            
        except Exception as e:
            logger.error(f"Error saving sessions: {str(e)}")
            
    def _dummy_encrypt(self, plaintext: str, key: bytes) -> bytes:
        """
        Placeholder encryption function for demonstration.
        
        Args:
            plaintext: Text to encrypt
            key: Encryption key
            
        Returns:
            Encrypted data
        """
        # This is a placeholder - do not use in production
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        
        # Use a fixed IV for demonstration (never do this in production!)
        iv = b'\x00' * 16
        
        # Create cipher and encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        # Return IV + ciphertext
        return iv + encrypted
        
    def _dummy_decrypt(self, ciphertext: bytes, key: bytes) -> str:
        """
        Placeholder decryption function for demonstration.
        
        Args:
            ciphertext: Data to decrypt
            key: Decryption key
            
        Returns:
            Decrypted text
        """
        # This is a placeholder - do not use in production
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        
        # Extract IV and ciphertext
        iv = ciphertext[:16]
        actual_ciphertext = ciphertext[16:]
        
        # Create cipher and decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(actual_ciphertext), AES.block_size)
        
        return decrypted.decode('utf-8')
