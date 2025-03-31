"""
WhatsApp registration client.

This module handles the WhatsApp registration process, including
requesting verification codes via SMS or voice call, and completing
registration to obtain credentials for the WhatsApp service.
"""

import logging
import time
import hashlib
import base64
import json
import os
import asyncio
from typing import Dict, Any, Optional, Tuple

import aiohttp

from bocksup.common.exceptions import RegistrationError
from bocksup.common.constants import WHATSAPP_SERVER, USER_AGENT

logger = logging.getLogger(__name__)

class RegistrationClient:
    """
    Client for WhatsApp account registration.
    
    This class manages the WhatsApp registration process, allowing users
    to register new accounts, request verification codes, and complete
    the verification process to obtain authentication credentials.
    """
    
    def __init__(self, country_code: str, phone_number: str):
        """
        Initialize the registration client.
        
        Args:
            country_code: Country code (e.g., '1' for USA)
            phone_number: Phone number without country code
        """
        self.country_code = country_code
        self.phone_number = phone_number
        
        # Combined phone number with country code
        self.full_phone = f"{country_code}{phone_number}"
        
        # Registration state
        self.registration_id = None
        self.identity_token = None
        self.request_token = None
        self.password = None
        self.expires = 0
        
    async def request_code(self, method: str = "sms", language: str = "en") -> bool:
        """
        Request a verification code.
        
        Args:
            method: Verification method ('sms' or 'voice')
            language: Language code for the verification message
            
        Returns:
            True if the request was successful
            
        Raises:
            RegistrationError: If the request fails
        """
        logger.info(f"Requesting {method} verification code for +{self.full_phone}")
        
        try:
            # Create registration ID if not already created
            if not self.registration_id:
                self.registration_id = self._generate_registration_id()
                
            # Create identity token
            self.identity_token = self._generate_identity_token()
            
            # Prepare request parameters
            params = {
                'cc': self.country_code,
                'in': self.phone_number,
                'method': method,
                'lg': language,
                'id': self.identity_token,
                'reg_id': self.registration_id
            }
            
            # Send request to WhatsApp servers
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'https://{WHATSAPP_SERVER}/v1/account/register/code',
                    json=params,
                    headers={'User-Agent': USER_AGENT}
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        error = result.get('error', 'Unknown error')
                        raise RegistrationError(f"Failed to request verification code: {error}")
                        
                    # Store request token
                    self.request_token = result.get('request_token')
                    
                    logger.info(f"Verification code requested successfully via {method}")
                    return True
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error requesting verification code: {str(e)}")
            raise RegistrationError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error requesting verification code: {str(e)}")
            raise RegistrationError(f"Failed to request verification code: {str(e)}")
            
    async def register(self, code: str) -> Dict[str, Any]:
        """
        Complete registration with verification code.
        
        Args:
            code: Verification code received via SMS or voice call
            
        Returns:
            Dictionary with registration credentials
            
        Raises:
            RegistrationError: If registration fails
        """
        logger.info(f"Registering phone number +{self.full_phone} with verification code")
        
        try:
            # Check if we have necessary tokens
            if not self.request_token or not self.identity_token:
                raise RegistrationError("Missing request token or identity token. Call request_code() first.")
                
            # Prepare request parameters
            params = {
                'cc': self.country_code,
                'in': self.phone_number,
                'code': code,
                'id': self.identity_token,
                'reg_id': self.registration_id,
                'request_token': self.request_token
            }
            
            # Send request to WhatsApp servers
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'https://{WHATSAPP_SERVER}/v1/account/register/verify',
                    json=params,
                    headers={'User-Agent': USER_AGENT}
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        error = result.get('error', 'Unknown error')
                        raise RegistrationError(f"Failed to register: {error}")
                        
                    # Extract registration details
                    self.password = result.get('password')
                    login = result.get('login')
                    expires = result.get('expires')
                    
                    if not self.password or not login:
                        raise RegistrationError("Registration successful but missing credentials in response")
                        
                    # Store expiration timestamp
                    self.expires = time.time() + (expires or 4294967296)
                    
                    # Create credentials dictionary
                    credentials = {
                        'phone': self.full_phone,
                        'password': self.password,
                        'login': login,
                        'expires': self.expires,
                        'registration_id': self.registration_id
                    }
                    
                    logger.info(f"Registration successful for +{self.full_phone}")
                    
                    return credentials
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during registration: {str(e)}")
            raise RegistrationError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            raise RegistrationError(f"Registration failed: {str(e)}")
            
    async def save_credentials(self, credentials: Optional[Dict[str, Any]] = None, path: str = '.') -> str:
        """
        Save registration credentials to a file.
        
        Args:
            credentials: Credentials to save (if None, uses the ones from registration)
            path: Directory to save the credentials file
            
        Returns:
            Path to the saved credentials file
            
        Raises:
            RegistrationError: If saving fails
        """
        try:
            # Use provided credentials or the ones from registration
            creds = credentials or {
                'phone': self.full_phone,
                'password': self.password,
                'expires': self.expires,
                'registration_id': self.registration_id
            }
            
            # Check if we have the necessary credentials
            if not creds.get('phone') or not creds.get('password'):
                raise RegistrationError("Missing required credentials")
                
            # Create filename based on phone number
            filename = f"whatsapp-{creds['phone']}.json"
            file_path = os.path.join(path, filename)
            
            # Write credentials to file
            with open(file_path, 'w') as f:
                json.dump(creds, f, indent=2)
                
            logger.info(f"Credentials saved to {file_path}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            raise RegistrationError(f"Failed to save credentials: {str(e)}")
            
    @staticmethod
    async def load_credentials(path: str) -> Dict[str, Any]:
        """
        Load registration credentials from a file.
        
        Args:
            path: Path to the credentials file
            
        Returns:
            Dictionary with registration credentials
            
        Raises:
            RegistrationError: If loading fails
        """
        try:
            # Check if file exists
            if not os.path.exists(path):
                raise RegistrationError(f"Credentials file not found: {path}")
                
            # Read credentials from file
            with open(path, 'r') as f:
                credentials = json.load(f)
                
            # Check if we have the necessary credentials
            if not credentials.get('phone') or not credentials.get('password'):
                raise RegistrationError("Missing required credentials in file")
                
            logger.info(f"Credentials loaded from {path}")
            
            return credentials
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in credentials file: {path}")
            raise RegistrationError(f"Invalid credentials file format")
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            raise RegistrationError(f"Failed to load credentials: {str(e)}")
            
    def _generate_registration_id(self) -> int:
        """
        Generate a registration ID.
        
        Returns:
            Registration ID
        """
        import random
        # Registration ID is a random 16-bit integer (excluding 0)
        return random.randint(1, 0xFFFF)
        
    def _generate_identity_token(self) -> str:
        """
        Generate an identity token.
        
        Returns:
            Identity token
        """
        # Create a deterministic identity token based on phone number
        token_data = f"{self.full_phone}:{self.registration_id}:{int(time.time())}"
        token_hash = hashlib.sha256(token_data.encode('utf-8')).digest()
        return base64.b64encode(token_hash).decode('utf-8')
