"""
Modul pentru gestionarea mesajelor WhatsApp.

Acest modul implementează funcționalitățile de bază pentru
trimiterea și primirea mesajelor prin rețeaua WhatsApp.
"""

import logging
import asyncio
import json
from typing import Dict, Callable, Optional, List, Union

import bocksup
from bocksup.auth.authenticator import Authenticator
from bocksup.layers.network.connection import WhatsAppConnection

logger = logging.getLogger(__name__)

class MessagingClient:
    """
    Client pentru trimiterea și primirea mesajelor WhatsApp.
    
    Această clasă oferă o interfață de nivel înalt pentru interacțiunea cu WhatsApp,
    inclusiv trimiterea de mesaje, primirea de notificări și gestionarea media.
    """
    
    def __init__(self, phone_number: str, password: Optional[str] = None):
        """
        Inițializează clientul de mesagerie.
        
        Args:
            phone_number: Numărul de telefon WhatsApp
            password: Parola sau token-ul WhatsApp (opțional pentru autentificare QR)
        """
        self._phone_number = phone_number
        self._password = password or ""  # Asigură că password nu este None
        self._connection = WhatsAppConnection()
        self._authenticator = Authenticator(phone_number, self._password)
        self._authenticator.set_lower(self._connection)
        self._connected = False
        self._authenticated = False
        self._message_handlers = []
        self._presence_handlers = []
        self._receipt_handlers = []
        
    async def connect(self) -> bool:
        """
        Conectare și autentificare cu WhatsApp.
        
        Returns:
            bool: True dacă conectarea și autentificarea au reușit
        """
        logger.info(f"Conectare la serverele WhatsApp cu numărul {self._phone_number}")
        
        # Conectare
        connected = await self._connection.connect()
        if not connected:
            logger.error("Conectarea la serverele WhatsApp a eșuat")
            return False
            
        self._connected = True
        logger.info("Conectat la serverele WhatsApp")
        
        # Autentificare
        try:
            authenticated = await self._authenticator.authenticate()
            if not authenticated:
                logger.error("Autentificarea a eșuat")
                self._authenticated = False
                return False
                
            self._authenticated = True
            logger.info("Autentificat cu succes la WhatsApp")
            
            # Înregistrăm handler-e implicite
            self._register_default_handlers()
            
            return True
            
        except bocksup.AuthenticationError as e:
            logger.error(f"Eroare de autentificare: {e}")
            self._authenticated = False
            return False
            
    async def disconnect(self) -> None:
        """
        Deconectare de la WhatsApp.
        """
        if self._connected:
            await self._connection.disconnect()
            self._connected = False
            self._authenticated = False
            logger.info("Deconectat de la serverele WhatsApp")
            
    async def send_text_message(self, to: str, text: str) -> Dict:
        """
        Trimite un mesaj text.
        
        Args:
            to: Numărul destinatarului sau JID
            text: Textul mesajului
            
        Returns:
            Dict conținând ID-ul mesajului și starea
            
        Raises:
            ConnectionError: Dacă nu sunteți conectat
            MessageError: Dacă trimiterea mesajului eșuează
        """
        if not self._connected or not self._authenticated:
            raise bocksup.ConnectionError("Nu sunteți conectat sau autentificat")
            
        try:
            # Asigurăm că numărul destinatarului este formatat corect
            if not to.endswith('@s.whatsapp.net'):
                to = bocksup.phone_to_jid(to)
                
            # Generare ID mesaj
            message_id = bocksup.generate_random_id()
            
            # Construire mesaj
            message_data = {
                "id": message_id,
                "type": "message",
                "to": to,
                "content": {
                    "type": "text",
                    "text": text
                },
                "timestamp": bocksup.timestamp_now()
            }
            
            # Trimitere mesaj
            logger.info(f"Trimitere mesaj către {to}")
            tag = await self._connection.send_message(message_data)
            
            # În mod normal, ar trebui să așteptăm o confirmare de la server
            # Dar pentru simplitate, presupunem că mesajul a fost trimis
            
            result = {
                "id": message_id,
                "status": "sent",
                "tag": tag
            }
            
            logger.info(f"Mesaj trimis cu ID: {message_id}")
            return result
            
        except Exception as e:
            logger.error(f"Eroare la trimiterea mesajului: {e}")
            raise bocksup.MessageError(f"Nu s-a putut trimite mesajul: {e}")
            
    def register_message_handler(self, handler: Callable) -> None:
        """
        Înregistrează un handler pentru mesajele primite.
        
        Args:
            handler: Funcția callback pentru tratarea mesajelor
        """
        self._message_handlers.append(handler)
        
    def register_presence_handler(self, handler: Callable) -> None:
        """
        Înregistrează un handler pentru actualizările de prezență.
        
        Args:
            handler: Funcția callback pentru tratarea actualizărilor de prezență
        """
        self._presence_handlers.append(handler)
        
    def register_receipt_handler(self, handler: Callable) -> None:
        """
        Înregistrează un handler pentru confirmările de mesaje.
        
        Args:
            handler: Funcția callback pentru tratarea confirmărilor
        """
        self._receipt_handlers.append(handler)
        
    def _register_default_handlers(self) -> None:
        """
        Înregistrează handler-e implicite pentru diverse tipuri de mesaje.
        """
        # Înregistrăm handler-ele în conexiune
        
        async def message_handler(data):
            """Handler pentru mesaje primite"""
            logger.debug(f"Mesaj primit: {data}")
            for handler in self._message_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Eroare în handler de mesaje: {e}")
        
        async def receipt_handler(data):
            """Handler pentru confirmări"""
            logger.debug(f"Confirmare primită: {data}")
            for handler in self._receipt_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Eroare în handler de confirmări: {e}")
        
        async def presence_handler(data):
            """Handler pentru actualizări de prezență"""
            logger.debug(f"Actualizare prezență: {data}")
            for handler in self._presence_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Eroare în handler de prezență: {e}")
                    
        # Înregistrăm handler-ele în conexiune
        self._connection.register_callback("message", message_handler)
        self._connection.register_callback("receipt", receipt_handler)
        self._connection.register_callback("presence", presence_handler)


def create_client(phone_number: str, password: Optional[str] = None) -> MessagingClient:
    """
    Creează un client WhatsApp pentru mesagerie.
    
    Args:
        phone_number: Numărul de telefon pentru contul WhatsApp
        password: Parola sau token-ul (opțional pentru autentificare QR)
        
    Returns:
        MessagingClient configurat
    """
    return MessagingClient(phone_number, password)