"""
Authenticator for WhatsApp servers.
"""

import logging
import time
import hashlib
import hmac
import base64
import os
import asyncio
from typing import Tuple, Dict, Optional, Any, Callable

from Crypto.Cipher import AES
import aiohttp

from bocksup.common.exceptions import AuthenticationError
from bocksup.common.constants import WHATSAPP_SERVER, USER_AGENT

logger = logging.getLogger(__name__)

class Authenticator:
    """
    Handles authentication with WhatsApp servers.
    
    This class manages credentials, generates authentication tokens,
    and handles the login flow with WhatsApp's authentication servers.
    """
    
    def __init__(self, phone_number: str, password: str):
        """
        Initialize the authenticator with WhatsApp credentials.
        
        Args:
            phone_number: Phone number in international format (e.g., 12025550108)
            password: Password or authentication token for WhatsApp
        """
        self.phone_number = phone_number
        self.password = password
        self.client_token = None
        self.server_token = None
        self.expires = 0
        self._connection = None
        
    async def authenticate(self) -> bool:
        """
        Authenticate with the WhatsApp server.
        
        Returns:
            bool: True if authentication was successful
        
        Raises:
            AuthenticationError: If authentication fails
        """
        logger.info(f"Authenticating phone number: {self.phone_number}")
        
        # Generate authentication tokens
        credentials = await self._generate_auth_credentials()
        
        try:
            # Connect to auth server
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': USER_AGENT,
                    'Content-Type': 'application/json'
                }
                
                auth_data = {
                    'phone': self.phone_number,
                    'auth_token': credentials['auth_token'],
                    'client_token': credentials['client_token'],
                    'device_id': self._generate_device_id()
                }
                
                # Send authentication request
                async with session.post(
                    f'https://{WHATSAPP_SERVER}/v1/auth', 
                    headers=headers,
                    json=auth_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Authentication failed with status {response.status}: {error_text}")
                        raise AuthenticationError(f"Authentication failed: {error_text}")
                    
                    result = await response.json()
                    
                    # Store authentication tokens
                    self.client_token = result.get('client_token')
                    self.server_token = result.get('server_token')
                    self.expires = time.time() + result.get('expires_in', 3600)
                    
                    logger.info("Authentication successful")
                    return True
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during authentication: {str(e)}")
            raise AuthenticationError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            raise AuthenticationError(f"Authentication error: {str(e)}")
    
    async def _generate_auth_credentials(self) -> Dict[str, str]:
        """
        Generate authentication credentials.
        
        Returns:
            Dict containing auth_token and client_token
        """
        client_token = base64.b64encode(os.urandom(20)).decode('utf-8')
        
        # Hash the password with the token
        key = hashlib.pbkdf2_hmac(
            'sha256', 
            self.password.encode('utf-8'), 
            self.phone_number.encode('utf-8'), 
            2000, 
            dklen=32
        )
        
        # Create auth token
        hmac_obj = hmac.new(key, client_token.encode('utf-8'), hashlib.sha256)
        auth_token = base64.b64encode(hmac_obj.digest()).decode('utf-8')
        
        return {
            'auth_token': auth_token,
            'client_token': client_token
        }
    
    def _generate_device_id(self) -> str:
        """
        Generate a device ID for authentication.
        
        Returns:
            str: A unique device identifier
        """
        # Generate a stable device ID based on the phone number
        device_hash = hashlib.md5(self.phone_number.encode('utf-8')).hexdigest()
        return f"Bocksup-{device_hash[:12]}"
    
    def is_authenticated(self) -> bool:
        """
        Check if the current authentication is still valid.
        
        Returns:
            bool: True if authenticated and not expired
        """
        return (self.client_token is not None and 
                self.server_token is not None and 
                time.time() < self.expires)
                
    async def refresh_authentication(self) -> bool:
        """
        Refresh authentication if it's expired or about to expire.
        
        Returns:
            bool: True if refresh was successful
        """
        # If token is expired or about to expire (within 5 minutes)
        if not self.is_authenticated() or time.time() > (self.expires - 300):
            logger.info("Authentication token expired or about to expire, refreshing...")
            return await self.authenticate()
        return True
