"""
WebSocket protocol implementation for WhatsApp.

This module handles the WebSocket-specific communication protocol
used by WhatsApp, including handshake, message format, and the
specific sequences needed for authentication and messaging.
"""

import json
import time
import logging
import asyncio
import base64
import uuid
import random
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

from bocksup.common.exceptions import ProtocolError, ConnectionError
from bocksup.common.constants import (
    CLIENT_VERSION, PROTOCOL_VERSION, WHATSAPP_WEBSOCKET_URL, USER_AGENT
)
from bocksup.common.utils import generate_random_id

logger = logging.getLogger(__name__)

class WebSocketProtocol:
    """
    Implementation of the WhatsApp WebSocket protocol.
    
    This class handles the format and sequence of messages required to
    communicate with WhatsApp servers using their WebSocket protocol.
    """
    
    def __init__(self):
        """Initialize the WebSocket protocol handler."""
        self.session_id = None
        self.client_id = f"Bocksup_{uuid.uuid4().hex[:8]}"
        self.message_counter = 0
        self.last_message_tag = None
        self.pending_messages = {}  # Message tags waiting for response
        self.challenge_data = None  # Used to store auth challenge during login
        self.pairing_code = None    # Used for phone pairing
        
    def create_handshake_message(self) -> str:
        """
        Create initial handshake message for WebSocket connection.
        
        Returns:
            JSON string with handshake message
        """
        self.session_id = generate_random_id(10)
        message_tag = f"{int(time.time())}.--{self.message_counter}"
        self.message_counter += 1
        self.last_message_tag = message_tag
        
        handshake = {
            "clientToken": self.client_id,
            "serverToken": None,  # Initially null, will be set after auth
            "clientId": f"python:{self.session_id}",
            "tag": message_tag,
            "type": "connect",
            "version": CLIENT_VERSION,
            "protocolVersion": PROTOCOL_VERSION,
            "connectType": "PHONE_CONNECTING",
            "connectReason": "USER_ACTIVATED",
            "features": {
                "supportsMultiDevice": True,
                "supportsE2EEncryption": True,
                "supportsQRLinking": True
            }
        }
        
        json_data = json.dumps(handshake)
        logger.debug(f"Created handshake: {json_data[:100]}...")
        return json_data
        
    def create_pairing_code_request(self, phone_number: str) -> str:
        """
        Create request for a pairing code.
        
        A pairing code is a short code (typically 8 digits) displayed on
        the phone that can be used to authenticate without scanning a QR code.
        
        Args:
            phone_number: Phone number in international format (e.g., 12025550108)
            
        Returns:
            JSON string with pairing code request
        """
        message_tag = f"{int(time.time())}.--{self.message_counter}"
        self.message_counter += 1
        self.last_message_tag = message_tag
        
        request = {
            "tag": message_tag,
            "type": "request",
            "method": "requestPairingCode",
            "params": {
                "phoneNumber": phone_number,
                "requestMeta": {
                    "platform": "python",
                    "deviceId": self.client_id,
                    "sessionId": self.session_id
                }
            }
        }
        
        json_data = json.dumps(request)
        logger.debug(f"Created pairing code request: {json_data[:100]}...")
        return json_data
        
    def create_pairing_code_verification(self, code: str) -> str:
        """
        Create verification message for pairing code authentication.
        
        Args:
            code: The pairing code received from the phone
            
        Returns:
            JSON string with verification message
        """
        if not self.challenge_data:
            raise ProtocolError("Missing challenge data for pairing verification")
            
        message_tag = f"{int(time.time())}.--{self.message_counter}"
        self.message_counter += 1
        self.last_message_tag = message_tag
        
        verification = {
            "tag": message_tag,
            "type": "response",
            "method": "verifyPairingCode",
            "params": {
                "code": code,
                "phoneNumber": self.challenge_data.get("phoneNumber", ""),
                "deviceId": self.client_id,
                "sessionId": self.session_id,
                "challengeToken": self.challenge_data.get("challengeToken", "")
            }
        }
        
        json_data = json.dumps(verification)
        logger.debug(f"Created pairing verification: {json_data[:100]}...")
        return json_data
        
    def create_keep_alive(self) -> str:
        """
        Create keep-alive message to maintain the WebSocket connection.
        
        Returns:
            JSON string with keep-alive message
        """
        message_tag = f"keepalive--{int(time.time())}"
        
        keepalive = {
            "tag": message_tag,
            "type": "ping",
            "timestamp": int(time.time())
        }
        
        return json.dumps(keepalive)
        
    def create_presence_update(self, presence_type: str = "available") -> str:
        """
        Create a presence update message.
        
        Args:
            presence_type: Type of presence (e.g., "available", "unavailable")
            
        Returns:
            JSON string with presence update
        """
        message_tag = f"{int(time.time())}.--{self.message_counter}"
        self.message_counter += 1
        
        presence = {
            "tag": message_tag,
            "type": "presence",
            "status": presence_type,
            "timestamp": int(time.time())
        }
        
        return json.dumps(presence)
        
    def process_message(self, message_data: Union[str, bytes]) -> Dict[str, Any]:
        """
        Process a message received from the WhatsApp server.
        
        Args:
            message_data: The received message data
            
        Returns:
            A dictionary with parsed message and metadata
            
        Raises:
            ProtocolError: If the message cannot be processed
        """
        try:
            # Parse the message
            if isinstance(message_data, bytes):
                # Try to decode as UTF-8 text first
                try:
                    message_text = message_data.decode('utf-8')
                except UnicodeDecodeError:
                    # Handle binary data (possibly encrypted or compressed)
                    return {
                        "type": "binary",
                        "data": message_data,
                        "timestamp": int(time.time())
                    }
            else:
                message_text = message_data
                
            # Parse JSON message
            message = json.loads(message_text)
            
            # Extract message type and tag
            message_type = message.get("type", "unknown")
            message_tag = message.get("tag", "")
            
            # Handle specific message types
            if message_type == "challenge":
                # This is an authentication challenge
                logger.info("Received authentication challenge")
                self.challenge_data = message.get("data", {})
                return {
                    "type": "challenge",
                    "challenge_type": self.challenge_data.get("type", "unknown"),
                    "tag": message_tag,
                    "timestamp": int(time.time())
                }
                
            elif message_type == "response":
                # Check if this is a pairing code response
                try:
                    if isinstance(message_text, str) and "pairingCode" in message_text:
                        message_data = message.get("data", {})
                        if isinstance(message_data, dict) and "pairingCode" in message_data:
                            self.pairing_code = message_data["pairingCode"]
                            logger.info(f"Received pairing code: {self.pairing_code}")
                            return {
                                "type": "pairing_code",
                                "code": self.pairing_code,
                                "tag": message_tag,
                                "timestamp": int(time.time())
                            }
                except (TypeError, AttributeError) as e:
                    logger.warning(f"Error processing pairing code: {e}")
                    
            elif message_type == "connected":
                # Connection confirmed
                logger.info("Connection confirmed by server")
                return {
                    "type": "connected",
                    "client_token": message.get("clientToken", ""),
                    "server_token": message.get("serverToken", ""),
                    "tag": message_tag,
                    "timestamp": int(time.time())
                }
                
            elif message_type == "message":
                # Regular message
                return {
                    "type": "message",
                    "content": message.get("content", {}),
                    "sender": message.get("sender", ""),
                    "tag": message_tag,
                    "timestamp": message.get("timestamp", int(time.time()))
                }
                
            elif message_type == "receipt":
                # Message receipt
                return {
                    "type": "receipt",
                    "receipt_type": message.get("receipt", ""),
                    "message_id": message.get("id", ""),
                    "sender": message.get("sender", ""),
                    "tag": message_tag,
                    "timestamp": message.get("timestamp", int(time.time()))
                }
                
            elif message_type == "presence":
                # Presence update
                return {
                    "type": "presence",
                    "presence_type": message.get("status", ""),
                    "sender": message.get("sender", ""),
                    "tag": message_tag,
                    "timestamp": message.get("timestamp", int(time.time()))
                }
                
            elif message_type == "error":
                # Error message
                logger.error(f"Received error from server: {message.get('error', {})}")
                return {
                    "type": "error",
                    "error_code": message.get("error", {}).get("code", 0),
                    "error_message": message.get("error", {}).get("message", "Unknown error"),
                    "tag": message_tag,
                    "timestamp": int(time.time())
                }
                
            # Handle unknown message types
            logger.debug(f"Unknown message type: {message_type}, data: {message_text[:100]}...")
            return {
                "type": message_type,
                "raw_data": message,
                "tag": message_tag,
                "timestamp": int(time.time())
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message as JSON: {str(e)}")
            return {
                "type": "parse_error",
                "error": str(e),
                "raw_data": message_data if isinstance(message_data, str) else "<binary data>",
                "timestamp": int(time.time())
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise ProtocolError(f"Failed to process message: {str(e)}")
            
    def create_text_message(self, recipient: str, text: str) -> str:
        """
        Create a text message to send.
        
        Args:
            recipient: The recipient's JID (e.g., 1234567890@s.whatsapp.net)
            text: The message text
            
        Returns:
            JSON string with text message
        """
        message_tag = f"{int(time.time())}.--{self.message_counter}"
        self.message_counter += 1
        message_id = f"MID.{uuid.uuid4().hex[:8]}"
        
        message = {
            "tag": message_tag,
            "type": "message",
            "recipient": recipient,
            "messageId": message_id,
            "content": {
                "type": "text",
                "text": text
            },
            "timestamp": int(time.time())
        }
        
        # Store pending message
        self.pending_messages[message_tag] = {
            "id": message_id,
            "recipient": recipient,
            "timestamp": int(time.time())
        }
        
        return json.dumps(message)
        
    def create_image_message(self, recipient: str, image_data: bytes, caption: Optional[str] = None) -> str:
        """
        Create an image message to send.
        
        Args:
            recipient: The recipient's JID (e.g., 1234567890@s.whatsapp.net)
            image_data: The binary image data
            caption: Optional text caption for the image
            
        Returns:
            JSON string with image message
        """
        message_tag = f"{int(time.time())}.--{self.message_counter}"
        self.message_counter += 1
        message_id = f"MID.{uuid.uuid4().hex[:8]}"
        
        # Convert image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        message = {
            "tag": message_tag,
            "type": "message",
            "recipient": recipient,
            "messageId": message_id,
            "content": {
                "type": "image",
                "image": image_base64,
                "caption": caption if caption else ""
            },
            "timestamp": int(time.time())
        }
        
        # Store pending message
        self.pending_messages[message_tag] = {
            "id": message_id,
            "recipient": recipient,
            "timestamp": int(time.time())
        }
        
        return json.dumps(message)
        
    def create_disconnect_message(self) -> str:
        """
        Create a disconnect message to gracefully end the session.
        
        Returns:
            JSON string with disconnect message
        """
        message_tag = f"disconnect--{int(time.time())}"
        
        disconnect = {
            "tag": message_tag,
            "type": "disconnect",
            "reason": "USER_INITIATED",
            "timestamp": int(time.time())
        }
        
        return json.dumps(disconnect)