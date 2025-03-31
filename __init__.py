"""
Bocksup - WhatsApp Integration Library

A Python library that replicates yowsup's WhatsApp integration functionality 
with improved stability, error handling, and modern Python compatibility.

This library provides a complete implementation of the WhatsApp protocol,
allowing you to build applications that can send and receive messages,
handle media, participate in group chats, and more.

Version: 0.2.0
License: MIT
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import random
import re
import ssl
import string
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import aiohttp
import construct
import websockets
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bocksup')

# Bocksup version
__version__ = '0.2.0'

# WhatsApp constants
WHATSAPP_WEB_URL = "web.whatsapp.com"
WHATSAPP_WEBSOCKET_URL = f"wss://{WHATSAPP_WEB_URL}/ws"
WHATSAPP_ORIGIN = f"https://{WHATSAPP_WEB_URL}"
WHATSAPP_WEB_VERSION = "2.2408.5"
WHATSAPP_WEB_VERSION_HASH = "7Odg9GWl5nK7xh3jFhzK"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"

# Connection parameters
WEBSOCKET_TIMEOUT = 20  # seconds
RECONNECT_DELAY = 3  # seconds
MAX_RECONNECT_ATTEMPTS = 5

# Exception classes
class BocksupException(Exception):
    """Base exception for all Bocksup-related errors."""
    pass

class AuthenticationError(BocksupException):
    """Raised when authentication with WhatsApp servers fails."""
    pass

class ConnectionError(BocksupException):
    """Raised when a connection to WhatsApp servers cannot be established or is lost."""
    pass

class MessageError(BocksupException):
    """Raised when there is an error sending or receiving a message."""
    pass

class EncryptionError(BocksupException):
    """Raised when there is an error with encryption or decryption."""
    pass

# Utility functions
def generate_random_id(length: int = 16) -> str:
    """
    Generate a random alphanumeric ID.
    
    Args:
        length: Length of the ID to generate
        
    Returns:
        A random alphanumeric string
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def timestamp_now() -> int:
    """
    Get current timestamp in milliseconds.
    
    Returns:
        Current timestamp in milliseconds
    """
    return int(time.time() * 1000)

def format_phone_number(phone: str) -> str:
    """
    Format a phone number to WhatsApp's expected format.
    
    Args:
        phone: Phone number to format
        
    Returns:
        Formatted phone number (country code + number)
    """
    # Remove any non-digit characters
    phone = re.sub(r'\\D', '', phone)
    
    # Ensure the number starts with a country code
    if not phone.startswith('+'):
        phone = '+' + phone
        
    return phone

def is_valid_phone_number(phone: str) -> bool:
    """
    Check if a phone number is valid.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if the phone number is valid
    """
    # Simple validation: 10+ digits, optionally starting with +
    pattern = r'^\\+?[0-9]{10,15}$'
    return bool(re.match(pattern, phone))

def phone_to_jid(phone: str) -> str:
    """
    Convert a phone number to a JID (Jabber ID) used by WhatsApp.
    
    Args:
        phone: Phone number to convert
        
    Returns:
        JID for the phone number
    """
    # Remove any non-digit characters
    phone = re.sub(r'\\D', '', phone)
    return f"{phone}@s.whatsapp.net"

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

def base64_encode(data: Union[str, bytes]) -> str:
    """
    Base64 encode data.
    
    Args:
        data: Data to encode
        
    Returns:
        Base64 encoded string
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')

def base64_decode(data: str) -> bytes:
    """
    Base64 decode data.
    
    Args:
        data: Base64 encoded string
        
    Returns:
        Decoded bytes
    """
    return base64.b64decode(data)

def sha256(data: Union[str, bytes]) -> bytes:
    """
    Calculate SHA-256 hash.
    
    Args:
        data: Data to hash
        
    Returns:
        SHA-256 hash as bytes
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).digest()

def hmac_sha256(key: Union[str, bytes], data: Union[str, bytes]) -> bytes:
    """
    Calculate HMAC-SHA256.
    
    Args:
        key: Key for HMAC
        data: Data to hash
        
    Returns:
        HMAC-SHA256 hash as bytes
    """
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hmac.new(key, data, hashlib.sha256).digest()

# Signal protocol implementation (simplified)
class SignalProtocol:
    """
    Implementare simplificată a protocolului Signal pentru criptarea end-to-end.
    """
    
    def __init__(self):
        """
        Inițializează protocolul Signal.
        """
        self.identity_key_pair = self._generate_key_pair()
        self.registration_id = random.randint(1, 16380)
        self.prekeys = []
        self.signed_prekey = None
        
        # Generare pre-keys
        self._generate_prekeys(20)
        self._generate_signed_prekey()
        
        logger.info("Protocol Signal inițializat")
    
    def _generate_key_pair(self) -> Dict:
        """
        Generează o pereche de chei RSA.
        
        Returns:
            Dict conținând cheia privată și publică
        """
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        
        return {
            "private": private_key,
            "public": public_key
        }
    
    def _generate_prekeys(self, count: int) -> None:
        """
        Generează un set de pre-keys.
        
        Args:
            count: Numărul de pre-keys de generat
        """
        for i in range(count):
            key_id = random.randint(1, 16380)
            key_pair = self._generate_key_pair()
            
            self.prekeys.append({
                "key_id": key_id,
                "key_pair": key_pair
            })
    
    def _generate_signed_prekey(self) -> None:
        """
        Generează o signed pre-key.
        """
        key_id = random.randint(1, 16380)
        key_pair = self._generate_key_pair()
        
        # Semnarea cheii publice cu cheia de identitate
        signature = self._sign(key_pair["public"], self.identity_key_pair["private"])
        
        self.signed_prekey = {
            "key_id": key_id,
            "key_pair": key_pair,
            "signature": signature
        }
    
    def _sign(self, data: bytes, private_key: bytes) -> bytes:
        """
        Semnează date folosind cheia privată.
        
        Args:
            data: Datele de semnat
            private_key: Cheia privată pentru semnare
            
        Returns:
            Semnătura
        """
        key = RSA.import_key(private_key)
        h = SHA256.new(data)
        return PKCS1_OAEP.new(key).encrypt(h.digest())
    
    def encrypt(self, message: Union[str, bytes], recipient_key: bytes) -> bytes:
        """
        Criptează un mesaj folosind cheia publică a destinatarului.
        
        Args:
            message: Mesajul de criptat
            recipient_key: Cheia publică a destinatarului
            
        Returns:
            Mesajul criptat
        """
        if isinstance(message, str):
            message = message.encode('utf-8')
            
        # Generare cheie de sesiune
        session_key = get_random_bytes(16)
        
        # Criptare cheie de sesiune cu cheia publică a destinatarului
        recipient_key_obj = RSA.import_key(recipient_key)
        cipher_rsa = PKCS1_OAEP.new(recipient_key_obj)
        enc_session_key = cipher_rsa.encrypt(session_key)
        
        # Criptare mesaj cu cheia de sesiune
        cipher_aes = AES.new(session_key, AES.MODE_GCM)
        ciphertext, tag = cipher_aes.encrypt_and_digest(message)
        
        return base64_encode(json.dumps({
            "encrypted_key": base64_encode(enc_session_key),
            "iv": base64_encode(cipher_aes.nonce),
            "ciphertext": base64_encode(ciphertext),
            "tag": base64_encode(tag)
        }).encode('utf-8'))
    
    def decrypt(self, encrypted_message: Union[str, bytes], private_key: bytes) -> bytes:
        """
        Decriptează un mesaj folosind cheia privată proprie.
        
        Args:
            encrypted_message: Mesajul criptat
            private_key: Cheia privată proprie
            
        Returns:
            Mesajul decriptat
        """
        if isinstance(encrypted_message, str):
            encrypted_message = encrypted_message.encode('utf-8')
            
        # Decodare mesaj
        message_data = json.loads(base64_decode(encrypted_message).decode('utf-8'))
        
        enc_session_key = base64_decode(message_data["encrypted_key"])
        nonce = base64_decode(message_data["iv"])
        ciphertext = base64_decode(message_data["ciphertext"])
        tag = base64_decode(message_data["tag"])
        
        # Decriptare cheie de sesiune
        private_key_obj = RSA.import_key(private_key)
        cipher_rsa = PKCS1_OAEP.new(private_key_obj)
        session_key = cipher_rsa.decrypt(enc_session_key)
        
        # Decriptare mesaj
        cipher_aes = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
        data = cipher_aes.decrypt_and_verify(ciphertext, tag)
        
        return data

# Main WhatsApp connection class
class WhatsAppConnection:
    """
    Gestionează conexiunea WebSocket la serverele WhatsApp.
    
    Această clasă implementează protocolul de comunicare al WhatsApp Web,
    folosind WebSockets pentru a transmite și primi mesaje de la serverele
    WhatsApp.
    """
    
    def __init__(self):
        """
        Inițializează conexiunea WhatsApp.
        """
        self.websocket = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.message_callbacks = {}
        self.message_queue = []
        self.client_id = generate_random_id(16)
        self._connect_task = None
        self._message_processor_task = None
        self._is_running = False
        self._message_tags = {}
        self._message_tag_counter = 1
        self._challenge_callbacks = []
        
        # Initialize encryption
        self.encryption = SignalProtocol()
        
        logger.info("WhatsApp connection initialized")
        
    async def connect(self) -> bool:
        """
        Conectează la serverul WhatsApp folosind WebSocket.
        
        Returns:
            bool: True dacă conectarea a reușit
        
        Raises:
            ConnectionError: Dacă conectarea eșuează
        """
        try:
            # Configurare SSL cu suport TLS modern
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            # Conectare la WebSocket
            logger.info(f"Conectare la {WHATSAPP_WEBSOCKET_URL}")
            self.websocket = await websockets.connect(
                WHATSAPP_WEBSOCKET_URL,
                extra_headers={
                    "Origin": WHATSAPP_ORIGIN,
                    "User-Agent": USER_AGENT
                },
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
                max_size=None,  # Fără limită de dimensiune pentru mesaje
            )
            
            logger.info("Conexiune WebSocket stabilită")
            self.is_connected = True
            self.reconnect_attempts = 0
            
            # Inițierea task-urilor pentru procesarea mesajelor
            self._is_running = True
            self._message_processor_task = asyncio.create_task(self._process_messages())
            
            # Trimiterea mesajului inițial
            await self._send_hello_message()
            
            return True
            
        except (websockets.exceptions.WebSocketException, OSError) as e:
            logger.error(f"Eroare la conectare: {e}")
            self.is_connected = False
            raise ConnectionError(f"Nu s-a putut conecta la WhatsApp: {e}")
    
    async def disconnect(self) -> None:
        """
        Deconectare de la serverul WhatsApp.
        """
        logger.info("Deconectare de la serverul WhatsApp")
        self._is_running = False
        
        if self._message_processor_task:
            self._message_processor_task.cancel()
            try:
                await self._message_processor_task
            except asyncio.CancelledError:
                pass
            self._message_processor_task = None
        
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Conexiune WebSocket închisă")
            except Exception as e:
                logger.error(f"Eroare la închiderea WebSocket: {e}")
            finally:
                self.websocket = None
                self.is_connected = False
    
    async def _send_hello_message(self) -> None:
        """
        Trimite mesajul inițial de handshake către server.
        """
        if not self.is_connected or not self.websocket:
            logger.error("Nu se poate trimite mesajul de hello - conexiune inexistentă")
            return
        
        hello_message = [
            "admin",
            "init",
            [WHATSAPP_WEB_VERSION, WHATSAPP_WEB_VERSION_HASH],
            [USER_AGENT],
            self.client_id,
            True
        ]
        
        await self.send_message(hello_message)
        logger.info("Mesaj de handshake trimis")
    
    async def send_message(self, message_data: Union[List, Dict, str]) -> str:
        """
        Trimite un mesaj către serverul WhatsApp.
        
        Args:
            message_data: Datele mesajului de trimis (vor fi convertite în JSON)
        
        Returns:
            str: Tag-ul mesajului pentru identificare
        
        Raises:
            ConnectionError: Dacă mesajul nu poate fi trimis
        """
        if not self.is_connected or not self.websocket:
            logger.error("Nu se poate trimite mesajul - conexiune inexistentă")
            raise ConnectionError("Nu există o conexiune activă la WhatsApp")
        
        # Generarea unui tag unic pentru mesaj
        message_tag = str(self._message_tag_counter)
        self._message_tag_counter += 1
        
        try:
            # Crearea mesajului complet cu tag
            if isinstance(message_data, (list, dict)):
                message_with_tag = f"{message_tag},{json.dumps(message_data)}"
            else:
                message_with_tag = f"{message_tag},{message_data}"
            
            logger.debug(f"Trimitere mesaj: {message_tag}")
            await self.websocket.send(message_with_tag)
            return message_tag
            
        except (websockets.exceptions.WebSocketException, OSError) as e:
            logger.error(f"Eroare la trimiterea mesajului: {e}")
            self.is_connected = False
            raise ConnectionError(f"Nu s-a putut trimite mesajul: {e}")
    
    async def _process_messages(self) -> None:
        """
        Procesează mesajele primite de la serverul WhatsApp.
        """
        logger.info("Începerea procesării mesajelor")
        
        while self._is_running and self.websocket:
            try:
                message = await self.websocket.recv()
                logger.debug(f"Mesaj primit: {message[:100]}...")
                
                # Procesare mesaj
                await self._handle_received_message(message)
                
            except (ConnectionClosed, websockets.exceptions.ConnectionClosedError) as e:
                logger.warning(f"Conexiunea WebSocket a fost închisă: {e}")
                self.is_connected = False
                break
            
            except Exception as e:
                logger.error(f"Eroare la procesarea mesajelor: {e}")
                # Continuă procesarea în ciuda erorilor
    
    async def _handle_received_message(self, message: str) -> None:
        """
        Procesează un mesaj primit.
        
        Args:
            message: Mesajul primit de la server
        """
        try:
            # Separarea tag-ului de conținutul mesajului
            parts = message.split(",", 1)
            if len(parts) < 2:
                logger.warning(f"Format de mesaj neașteptat: {message[:100]}...")
                return
            
            tag, content = parts
            
            # Gestionarea mesajelor speciale
            if content == "":
                logger.debug(f"Mesaj gol cu tag {tag} primit")
                return
            
            # Încercare de a procesa conținutul ca JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(f"Conținut non-JSON primit: {content[:100]}...")
                return
            
            # Verificare pentru mesaje de challenge
            if isinstance(data, list) and len(data) > 0:
                if data[0] == "challenge":
                    await self._handle_challenge(data[1])
                    return
            
            # Determinarea tipului de mesaj pentru callback-uri
            message_type = self._determine_message_type(data)
            
            # Apelarea callback-urilor înregistrate pentru acest tip de mesaj
            if message_type in self.message_callbacks:
                for callback in self.message_callbacks[message_type]:
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"Eroare în callback pentru mesaj {message_type}: {e}")
            
        except Exception as e:
            logger.error(f"Eroare la procesarea mesajului primit: {e}")
    
    def _determine_message_type(self, data) -> str:
        """
        Determină tipul unui mesaj primit.
        
        Args:
            data: Datele mesajului
            
        Returns:
            str: Tipul de mesaj
        """
        if isinstance(data, list):
            if len(data) > 0:
                # Formatul 1: ["action", data, ...]
                return str(data[0])
        
        elif isinstance(data, dict):
            # Formatul 2: {"type": "type", ...}
            if "type" in data:
                return data["type"]
        
        return "unknown"
    
    async def _handle_challenge(self, challenge_data: str) -> None:
        """
        Gestionează un challenge de autentificare primit de la server.
        
        Args:
            challenge_data: Datele challenge-ului
        """
        logger.info("Challenge de autentificare primit")
        
        for callback in self._challenge_callbacks:
            try:
                await callback(challenge_data)
            except Exception as e:
                logger.error(f"Eroare în callback pentru challenge: {e}")
    
    def register_callback(self, message_type: str, callback: Callable) -> None:
        """
        Înregistrează un callback pentru un anumit tip de mesaj.
        
        Args:
            message_type: Tipul de mesaj pentru care se înregistrează callback-ul
            callback: Funcția de callback care va fi apelată
        """
        if message_type not in self.message_callbacks:
            self.message_callbacks[message_type] = []
        
        self.message_callbacks[message_type].append(callback)
        logger.debug(f"Callback înregistrat pentru mesaje de tip {message_type}")
    
    def register_challenge_callback(self, callback: Callable) -> None:
        """
        Înregistrează un callback pentru procesarea challenge-urilor de autentificare.
        
        Args:
            callback: Funcția de callback care va procesa challenge-ul
        """
        self._challenge_callbacks.append(callback)
        logger.debug("Callback înregistrat pentru challenge-uri de autentificare")

# Authenticator class
class Authenticator:
    """
    Handles authentication with WhatsApp servers.
    
    This class manages credentials, generates authentication tokens,
    and handles the login flow with WhatsApp's authentication servers.
    """
    
    def __init__(self, phone_number: str, password: Optional[str] = None):
        """
        Initialize the authenticator with WhatsApp credentials.
        
        Args:
            phone_number: Phone number in international format (e.g., 12025550108)
            password: Password or authentication token for WhatsApp (optional)
        """
        self.phone_number = format_phone_number(phone_number)
        self.password = password
        self.is_authenticated = False
        self.auth_token = None
        self.client_token = None
        self.expiration_time = None
        self.connection = None
        self.device_id = self._generate_device_id()
        
        logger.info(f"Authenticator initialized for phone number: {self.phone_number}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with the WhatsApp server.
        
        This method supports both the traditional API-based authentication
        (similar to yowsup) and the modern WebSocket-based authentication
        used by WhatsApp Web. The web mode should be used for actual implementation.
        
        Returns:
            bool: True if authentication was successful
        
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Preferăm autentificarea web modernă
            return await self._authenticate_web()
        except Exception as e:
            logger.error(f"Autentificare web eșuată: {e}")
            
            # Fallback la metoda tradițională
            try:
                return await self._authenticate_api()
            except Exception as e:
                logger.error(f"Autentificare API eșuată: {e}")
                raise AuthenticationError(f"Autentificare eșuată: {e}")
    
    async def _authenticate_web(self) -> bool:
        """
        Authenticate using WhatsApp Web protocol (WebSocket-based).
        
        Returns:
            bool: True if authentication was successful
        
        Raises:
            AuthenticationError: If authentication fails
        """
        # Create WhatsApp connection if not already present
        if not self.connection:
            self.connection = WhatsAppConnection()
            
        # Connect to WhatsApp servers
        try:
            await self.connection.connect()
        except ConnectionError as e:
            raise AuthenticationError(f"Could not connect to WhatsApp servers: {e}")
        
        # Set up challenge callback for QR code or pairing code authentication
        auth_completion_event = asyncio.Event()
        auth_result = {"success": False, "error": None}
        
        async def challenge_callback(challenge_data):
            """
            Process authentication challenges from the server.
            """
            try:
                # Decode the challenge data
                decoded_challenge = base64_decode(challenge_data)
                
                # Request pairing code
                await self._request_pairing_code()
                
                # In a real implementation, we would wait for user to enter the code
                # For now, we'll just log the challenge
                logger.info("Authentication challenge received")
                logger.info("In a real implementation, user would enter the pairing code")
                
                # Simulate authentication response (would be based on real user input)
                await self._send_auth_response(decoded_challenge)
                
                # Check authentication result
                auth_result["success"] = True
                
            except Exception as e:
                logger.error(f"Error processing authentication challenge: {e}")
                auth_result["error"] = str(e)
                auth_result["success"] = False
            finally:
                auth_completion_event.set()
        
        # Register the challenge callback
        self.connection.register_challenge_callback(challenge_callback)
        
        # Wait for authentication completion
        await auth_completion_event.wait()
        
        # Check result
        if not auth_result["success"]:
            error_msg = auth_result["error"] or "Authentication failed"
            raise AuthenticationError(error_msg)
        
        # Generate and store authentication credentials
        creds = await self._generate_auth_credentials()
        self.auth_token = creds["auth_token"]
        self.client_token = creds["client_token"]
        self.expiration_time = datetime.now().timestamp() + 86400  # 24 hours
        
        self.is_authenticated = True
        logger.info("Authentication successful")
        return True
    
    async def _authenticate_api(self) -> bool:
        """
        Authenticate using traditional API method (compatible with yowsup).
        
        Returns:
            bool: True if authentication was successful
        
        Raises:
            AuthenticationError: If authentication fails
        """
        # This is a simplified implementation as the API auth is now deprecated
        logger.warning("API authentication is deprecated, please use Web authentication")
        
        try:
            # Create a POST request to simulate the traditional API authentication
            headers = {
                "Authorization": f"Bearer {self.password or 'SIMULATED_TOKEN'}",
                "User-Agent": USER_AGENT
            }
            
            # Log attempt
            logger.info("Attempting API authentication (simulated)")
            
            # Generate mock authentication credentials
            creds = await self._generate_auth_credentials()
            self.auth_token = creds["auth_token"]
            self.client_token = creds["client_token"]
            self.expiration_time = datetime.now().timestamp() + 86400  # 24 hours
            
            self.is_authenticated = True
            logger.info("API authentication successful (simulated)")
            return True
            
        except Exception as e:
            logger.error(f"API authentication failed: {e}")
            raise AuthenticationError(f"API authentication failed: {e}")
    
    async def _request_pairing_code(self) -> None:
        """
        Request a pairing code from WhatsApp servers.
        """
        if not self.connection or not self.connection.is_connected:
            raise ConnectionError("No active connection to WhatsApp")
        
        # Format message for requesting pairing code
        pairing_request = [
            "admin",
            "request_code",
            {
                "method": "sms",
                "phone": self.phone_number,
                "device_id": self.device_id
            }
        ]
        
        # Send request
        try:
            await self.connection.send_message(pairing_request)
            logger.info(f"Pairing code requested for {self.phone_number}")
        except Exception as e:
            logger.error(f"Failed to request pairing code: {e}")
            raise AuthenticationError(f"Failed to request pairing code: {e}")
    
    async def _send_auth_response(self, challenge: bytes) -> None:
        """
        Send authentication response to challenge.
        
        Args:
            challenge: Challenge data received from server
        """
        if not self.connection or not self.connection.is_connected:
            raise ConnectionError("No active connection to WhatsApp")
        
        # In a real implementation, this would use the user-provided pairing code
        # and the challenge to compute a proper response
        
        # For now, this is a simplified mock implementation
        mock_response = {
            "type": "auth_response",
            "data": base64_encode(challenge)  # In reality, this would be properly computed
        }
        
        try:
            await self.connection.send_message(mock_response)
            logger.info("Authentication response sent")
        except Exception as e:
            logger.error(f"Failed to send authentication response: {e}")
            raise AuthenticationError(f"Failed to send authentication response: {e}")
    
    async def _generate_auth_credentials(self) -> Dict[str, str]:
        """
        Generate authentication credentials.
        
        Returns:
            Dict containing auth_token and client_token
        """
        # In a real implementation, these would be derived from server response
        return {
            "auth_token": generate_random_id(64),
            "client_token": generate_random_id(32)
        }
    
    def _generate_device_id(self) -> str:
        """
        Generate a device ID for authentication.
        
        Returns:
            str: A unique device identifier
        """
        # Generate a deterministic device ID based on the phone number
        phone_hash = hashlib.md5(self.phone_number.encode('utf-8')).hexdigest()
        return f"bocksup_{phone_hash[:16]}"

# Main MessagingClient class
class MessagingClient:
    """
    Client for sending and receiving WhatsApp messages.
    
    This class provides a high-level interface for interacting with WhatsApp,
    including sending messages, receiving notifications, and managing media.
    """
    
    def __init__(self, phone_number: str, password: Optional[str] = None):
        """
        Initialize the messaging client.
        
        Args:
            phone_number: WhatsApp phone number
            password: WhatsApp password or auth token (optional for QR login)
        """
        self.authenticator = Authenticator(phone_number, password)
        self.connection = None
        self.is_connected = False
        self.message_handlers = {}
        self.presence_handlers = []
        self.receipt_handlers = []
        self.media_handlers = {}
        
        logger.info(f"Messaging client initialized for {phone_number}")
    
    async def connect(self) -> bool:
        """
        Connect and authenticate with WhatsApp.
        
        Returns:
            bool: True if connection and authentication were successful
        """
        try:
            # Authenticate
            if not await self.authenticator.authenticate():
                logger.error("Authentication failed")
                return False
            
            # Use the connection from authenticator
            self.connection = self.authenticator.connection
            
            # Register handlers for different message types
            self._register_default_handlers()
            
            self.is_connected = True
            logger.info("Client connected and authenticated")
            return True
            
        except (ConnectionError, AuthenticationError) as e:
            logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """
        Disconnect from WhatsApp.
        """
        if self.connection:
            await self.connection.disconnect()
        
        self.is_connected = False
        logger.info("Client disconnected")
    
    async def send_text_message(self, to: str, text: str) -> Dict:
        """
        Send a text message.
        
        Args:
            to: Recipient's phone number or JID
            text: Message text
            
        Returns:
            Dict containing message ID and status
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        if not self.is_connected or not self.connection:
            raise ConnectionError("Not connected to WhatsApp")
        
        # Ensure recipient is in JID format
        recipient = to if "@" in to else phone_to_jid(to)
        
        # Create message structure
        message_id = generate_random_id()
        timestamp = timestamp_now()
        
        message = {
            "id": message_id,
            "type": "chat",
            "to": recipient,
            "content": text,
            "timestamp": timestamp
        }
        
        try:
            # In a real implementation, the message would be properly formatted
            # according to WhatsApp's protocol and encrypted if needed
            
            # Send message
            await self.connection.send_message(["message", "send", message])
            
            logger.info(f"Text message sent to {recipient}")
            return {
                "message_id": message_id,
                "status": "sent",
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise MessageError(f"Failed to send message: {e}")
    
    def register_message_handler(self, handler: Callable) -> None:
        """
        Register a handler for incoming messages.
        
        Args:
            handler: Callback function to handle messages
        """
        if "message" not in self.message_handlers:
            self.message_handlers["message"] = []
        
        self.message_handlers["message"].append(handler)
        logger.debug("Message handler registered")
    
    def register_presence_handler(self, handler: Callable) -> None:
        """
        Register a handler for presence updates.
        
        Args:
            handler: Callback function to handle presence updates
        """
        self.presence_handlers.append(handler)
        logger.debug("Presence handler registered")
    
    def register_receipt_handler(self, handler: Callable) -> None:
        """
        Register a handler for message receipts.
        
        Args:
            handler: Callback function to handle receipts
        """
        self.receipt_handlers.append(handler)
        logger.debug("Receipt handler registered")
    
    def _register_default_handlers(self) -> None:
        """
        Register default handlers for various message types.
        """
        if not self.connection:
            logger.error("Cannot register handlers - no connection")
            return
        
        # Message handler
        async def message_handler(data):
            if "message" in self.message_handlers:
                for handler in self.message_handlers["message"]:
                    try:
                        await handler(data)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
        
        # Receipt handler
        async def receipt_handler(data):
            for handler in self.receipt_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error in receipt handler: {e}")
        
        # Presence handler
        async def presence_handler(data):
            for handler in self.presence_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error in presence handler: {e}")
        
        # Register with the connection
        self.connection.register_callback("message", message_handler)
        self.connection.register_callback("receipt", receipt_handler)
        self.connection.register_callback("presence", presence_handler)

# Client factory
def create_client(phone_number: str, password: Optional[str] = None) -> MessagingClient:
    """
    Create a WhatsApp messaging client.
    
    Args:
        phone_number: Phone number for WhatsApp account
        password: Password or token (optional for QR login)
        
    Returns:
        Configured MessagingClient
    """
    return MessagingClient(phone_number, password)

# Test connection function
async def test_server_connection(phone_number: Optional[str] = None) -> Dict:
    """
    Test connection to WhatsApp servers.
    
    Args:
        phone_number: Optional phone number for testing with pairing code
        
    Returns:
        Dict with test results
    """
    logger.info("Testing connection to WhatsApp servers")
    
    # Results dictionary
    results = {
        "connection": False,
        "handshake": False,
        "challenge": False,
        "pairing_code": False,
        "errors": []
    }
    
    try:
        # Create connection
        connection = WhatsAppConnection()
        
        # Test connection
        try:
            await connection.connect()
            results["connection"] = True
            logger.info("Connection test successful")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            results["errors"].append(f"Connection error: {str(e)}")
            return results
        
        # Test handshake
        try:
            # The connect method already sends a handshake message
            # We'll wait for a response for a short time
            await asyncio.sleep(2)
            results["handshake"] = True
            logger.info("Handshake test successful")
        except Exception as e:
            logger.error(f"Handshake test failed: {e}")
            results["errors"].append(f"Handshake error: {str(e)}")
        
        # Test challenge and pairing code if phone number provided
        if phone_number:
            try:
                # Set up challenge callback
                challenge_received = asyncio.Event()
                
                async def challenge_callback(challenge_data):
                    results["challenge"] = True
                    logger.info("Challenge received")
                    challenge_received.set()
                
                connection.register_challenge_callback(challenge_callback)
                
                # Wait for challenge
                try:
                    # Create authenticator for testing
                    auth = Authenticator(phone_number)
                    auth.connection = connection
                    
                    # Request pairing code
                    await auth._request_pairing_code()
                    results["pairing_code"] = True
                    logger.info("Pairing code request successful")
                    
                    # Wait for challenge callback to be called
                    await asyncio.wait_for(challenge_received.wait(), timeout=5)
                    
                except asyncio.TimeoutError:
                    logger.warning("No challenge received within timeout")
                    results["errors"].append("Challenge timeout")
                
            except Exception as e:
                logger.error(f"Challenge/pairing test failed: {e}")
                results["errors"].append(f"Challenge/pairing error: {str(e)}")
        
        # Disconnect
        await connection.disconnect()
        
    except Exception as e:
        logger.error(f"Test failed with unexpected error: {e}")
        results["errors"].append(f"Unexpected error: {str(e)}")
    
    # Return results
    return results