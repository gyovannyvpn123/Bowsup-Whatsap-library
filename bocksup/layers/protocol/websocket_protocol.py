"""
Protocol WebSocket pentru comunicarea cu serverele WhatsApp.

Acest modul implementează protocolul specific WhatsApp peste WebSocket,
gestionând structura mesajelor, formatarea, și procesarea datelor.
"""

import time
import random
import json
import logging
import uuid
from typing import Dict, Any, Optional, Union, Callable, List, Tuple

from ...common.constants import (
    DEFAULT_CLIENT_VERSION, 
    WA_PROTOCOL_VERSION,
    DEFAULT_PLATFORM,
    BINARY_TYPE_HANDSHAKE,
    BINARY_TYPE_PAIRING,
    BINARY_TYPE_JSON
)
from ...common.exceptions import ProtocolError, BocksupError
from ...utils.binary_utils import (
    encode_binary_message,
    decode_binary_message,
    encode_json_message_binary,
    encode_handshake_binary,
    encode_pairing_request_binary
)

logger = logging.getLogger(__name__)

class WebSocketProtocol:
    """
    Protocol pentru comunicarea cu serverele WhatsApp prin WebSocket.
    
    Această clasă gestionează formatarea și parsarea mesajelor pentru protocolul
    WebSocket specific WhatsApp, implementând handshake-ul și mesajele binare.
    """
    
    def __init__(self, 
                 client_id: str = None,
                 client_version: str = DEFAULT_CLIENT_VERSION,
                 protocol_version: str = WA_PROTOCOL_VERSION,
                 platform: str = DEFAULT_PLATFORM):
        """
        Inițializează protocolul WebSocket.
        
        Args:
            client_id: ID client unic, generat automat dacă nu este furnizat
            client_version: Versiunea client WhatsApp de emulat
            protocol_version: Versiunea protocolului WhatsApp
            platform: Platforma client (android, web, etc.)
        """
        self.client_id = client_id or str(uuid.uuid4())
        self.client_version = client_version
        self.protocol_version = protocol_version
        self.platform = platform
        self.server_token = None
        self.message_tag_counter = 0
        self.pairing_code = None
        
    def generate_tag(self) -> str:
        """
        Generează un tag unic pentru mesaje.
        
        Returns:
            str: Tag unic
        """
        tag = f"{int(time.time())}.--{self.message_tag_counter}"
        self.message_tag_counter += 1
        return tag
    
    def create_handshake_message(self) -> Dict[str, Any]:
        """
        Creează un mesaj de handshake pentru inițierea conexiunii.
        
        Returns:
            Dict conținând datele handshake
        """
        handshake = {
            "clientId": self.client_id,
            "connectType": "WIFI_UNKNOWN",
            "connectReason": "USER_ACTIVATED",
            "userAgent": {
                "platform": self.platform,
                "releaseChannel": "RELEASE",
                "version": self.client_version,
                "deviceName": "Bocksup",
                "manufacturer": "Bocksup",
                "osVersion": "13",
                "mcc": "000",
                "mnc": "000",
                "osName": "Android",
                "localeLanguageIso6391": "ro",
                "localeCountryIso31661Alpha2": "RO"
            },
            "webInfo": {
                "webSubPlatform": "WEB_BROWSER"
            },
            "timeout": 60000,
            "passive": True,
            "username": self.client_id
        }
        
        return handshake
    
    def create_handshake_binary(self) -> bytes:
        """
        Creează mesajul binar de handshake pentru serverul WhatsApp.
        
        Returns:
            bytes: Mesajul binar de handshake
        """
        handshake_data = self.create_handshake_message()
        return encode_handshake_binary(handshake_data)
    
    def create_pairing_request(self, phone_number: str, method: str = "sms") -> Dict[str, Any]:
        """
        Creează un mesaj de solicitare cod de asociere.
        
        Args:
            phone_number: Numărul de telefon în format internațional
            method: Metoda de trimitere a codului (sms sau voice)
            
        Returns:
            Dict conținând datele cererii
        """
        # Format număr de telefon (elimină prefixul '+' dacă există)
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Creează obiectul de cerere
        pairing_request = {
            "messageType": "request_pairing_code",
            "phoneNumber": phone_number,
            "isPrimaryDevice": True,
            "method": method
        }
        
        return pairing_request
    
    def create_pairing_request_binary(self, phone_number: str, method: str = "sms") -> bytes:
        """
        Creează mesajul binar de solicitare cod de asociere.
        
        Args:
            phone_number: Numărul de telefon în format internațional
            method: Metoda de trimitere a codului (sms sau voice)
            
        Returns:
            bytes: Mesajul binar de solicitare cod
        """
        return encode_pairing_request_binary(phone_number, method)
    
    def create_json_message_binary(self, data: Dict[str, Any]) -> bytes:
        """
        Creează un mesaj JSON binar.
        
        Args:
            data: Datele JSON de codificat
            
        Returns:
            bytes: Mesajul binar
        """
        return encode_json_message_binary(data)
        
    def create_keep_alive(self) -> Dict[str, Any]:
        """
        Creează un mesaj de keep-alive.
        
        Returns:
            Dict conținând mesajul keep-alive
        """
        return {
            "tag": self.generate_tag(),
            "type": "keep_alive"
        }
    
    def process_message(self, message: bytes) -> Tuple[Optional[int], Any]:
        """
        Procesează un mesaj binar de la server.
        
        Args:
            message: Mesajul binar primit
            
        Returns:
            Tuple conținând (tip_mesaj, date_decodate)
        """
        try:
            message_type, decoded_data = decode_binary_message(message)
            
            # Procesează anumite tipuri de mesaje special
            if message_type == BINARY_TYPE_PAIRING:
                # Extrage codul de asociere dacă este prezent
                if isinstance(decoded_data, dict) and decoded_data.get("pairingCode"):
                    self.pairing_code = decoded_data.get("pairingCode")
                    logger.info(f"Cod de asociere primit: {self.pairing_code}")
            
            return message_type, decoded_data
            
        except Exception as e:
            logger.error(f"Eroare la procesarea mesajului: {str(e)}")
            return None, message