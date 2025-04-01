"""
Conexiune la serverele WhatsApp.

Acest modul gestionează conexiunea WebSocket la serverele WhatsApp,
inclusiv handshake-ul inițial, autentificarea și mesajele.
"""

import asyncio
import time
import json
import random
import logging
import uuid
from typing import Dict, Any, Optional, Union, Callable, List, Tuple, NoReturn

# Biblioteci externe
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed

# Module Bocksup
from ...common.constants import (
    WA_WEBSOCKET_URL,
    CONN_STATE_DISCONNECTED,
    CONN_STATE_CONNECTING,
    CONN_STATE_CONNECTED,
    CONN_STATE_AUTHENTICATED,
    CONN_STATE_ERROR,
    BINARY_TYPE_HANDSHAKE,
    BINARY_TYPE_JSON,
    BINARY_TYPE_CHALLENGE,
    KEEP_ALIVE_INTERVAL,
    CONNECTION_TIMEOUT
)
from ...common.exceptions import ConnectionError, ProtocolError, BocksupError
from ..protocol.websocket_protocol import WebSocketProtocol
from ...utils.binary_utils import (
    encode_binary_message,
    decode_binary_message,
    encode_json_message_binary
)

logger = logging.getLogger(__name__)

class SignalProtocol: # Placeholder -  This class needs to be implemented separately.
    pass


class WhatsAppConnection:
    """
    Gestionează conexiunea WebSocket la serverele WhatsApp.

    Această clasă implementează conexiunea la nivel de rețea,
    gestionând WebSocket-uri, recuperare la erori, și trimiterea
    mesajelor formulate corespunzător.
    """

    def __init__(self, session_id: str = None, url: str = WA_WEBSOCKET_URL,
                 client_token: str = None, server_token: str = None):
        """
        Inițializează o conexiune la serverele WhatsApp.

        Args:
            session_id: Identificator de sesiune unic, generat automat dacă nu este specificat
            url: URL-ul serverului WebSocket WhatsApp
            client_token: Token client opțional pentru reconectare
            server_token: Token server opțional pentru reconectare
        """
        self.connection_id = session_id or f"bocksup_ws_{uuid.uuid4().hex[:8]}"
        self.server_url = url
        self.client_token = client_token
        self.server_token = server_token

        # Stare conexiune
        self.connection_state = CONN_STATE_DISCONNECTED
        self.is_connected = False
        self.last_activity = 0
        self.retry_count = 0
        self.max_retries = 3

        # Resurse conexiune
        self._websocket = None
        self._keepalive_task = None
        self._message_handler_task = None
        self.signal_protocol = SignalProtocol()

        # Callbacks
        self._message_callbacks = {}
        self._challenge_callback = None
        self._on_connect_callback = None
        self._on_disconnect_callback = None

        # Protocol
        self.protocol = WebSocketProtocol(client_id=self.connection_id)

    async def connect(self) -> bool:
        """
        Conectare la serverul WhatsApp cu retry automat.

        Returns:
            bool: True dacă conexiunea a fost stabilită cu succes

        Raises:
            ConnectionError: Dacă nu se poate conecta la server
        """
        while self.retry_count < self.max_retries:
            try:
                if self.is_connected:
                    logger.warning(f"[{self.connection_id}] Deja conectat la server")
                    return True
                self.connection_state = CONN_STATE_CONNECTING

                logger.info(f"[{self.connection_id}] Conectare la {self.server_url}...")

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
                    "Origin": "https://web.whatsapp.com",
                    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7"
                }
                
                self._websocket = await websockets.connect(
                    self.server_url,
                    additional_headers=headers,
                    ping_interval=20,
                    ping_timeout=30,
                    max_size=None,
                    close_timeout=10
                )

                # Actualizare stare
                self.connection_state = CONN_STATE_CONNECTED
                self.is_connected = True
                self.last_activity = time.time()
                self.retry_count = 0

                logger.info(f"[{self.connection_id}] Conectat cu succes la server")

                # Start message handler
                self._message_handler_task = asyncio.create_task(self._message_handler())

                # Start keepalive
                self._keepalive_task = asyncio.create_task(self._keepalive_loop())

                # Apelare callback conectare dacă există
                if self._on_connect_callback:
                    await self._on_connect_callback()

                return True

            except Exception as e:
                self.retry_count += 1
                logger.error(f"[{self.connection_id}] Eroare la conectare (încercare {self.retry_count}): {str(e)}")
                self.connection_state = CONN_STATE_ERROR
                self.is_connected = False
                await asyncio.sleep(2 ** self.retry_count)

        logger.error(f"[{self.connection_id}] Număr maxim de încercări depășit.")
        raise ConnectionError(f"Failed to connect to WhatsApp server after multiple retries.")


    async def disconnect(self) -> None:
        """
        Deconectare de la serverul WhatsApp.
        """
        try:
            logger.info(f"[{self.connection_id}] Deconectare...")

            # Anulare task-uri
            if self._keepalive_task:
                self._keepalive_task.cancel()
                try:
                    await self._keepalive_task
                except asyncio.CancelledError:
                    pass
                self._keepalive_task = None

            if self._message_handler_task:
                self._message_handler_task.cancel()
                try:
                    await self._message_handler_task
                except asyncio.CancelledError:
                    pass
                self._message_handler_task = None

            # Închidere WebSocket
            if self._websocket:
                await self._websocket.close()
                self._websocket = None

            # Actualizare stare
            self.connection_state = CONN_STATE_DISCONNECTED
            self.is_connected = False

            logger.info(f"[{self.connection_id}] Deconectat de la server")

            # Apelare callback deconectare dacă există
            if self._on_disconnect_callback:
                await self._on_disconnect_callback()

        except Exception as e:
            logger.error(f"[{self.connection_id}] Eroare la deconectare: {str(e)}")
            self.connection_state = CONN_STATE_ERROR

    async def _keepalive_loop(self) -> NoReturn:
        """
        Buclă pentru trimiterea mesajelor keep-alive periodice.

        Această funcție rulează în fundal și trimite mesaje keep-alive
        pentru a menține conexiunea deschisă.
        """
        try:
            while self.is_connected:
                # Verifică dacă a trecut suficient timp de la ultima activitate
                current_time = time.time()
                time_since_last_activity = current_time - self.last_activity

                if time_since_last_activity >= KEEP_ALIVE_INTERVAL:
                    # Trimite mesaj keep-alive
                    try:
                        keepalive_message = self.protocol.create_keep_alive()
                        await self.send_message(keepalive_message)
                        logger.debug(f"[{self.connection_id}] Mesaj keep-alive trimis")
                    except Exception as e:
                        logger.error(f"[{self.connection_id}] Eroare la trimiterea mesajului keep-alive: {str(e)}")

                # Așteaptă înainte de următoarea verificare
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            # Task anulat, se iese din buclă
            logger.debug(f"[{self.connection_id}] Buclă keep-alive oprită")
        except Exception as e:
            logger.error(f"[{self.connection_id}] Eroare în bucla keep-alive: {str(e)}")

    async def _message_handler(self) -> NoReturn:
        """
        Buclă pentru procesarea mesajelor primite de la server.

        Această funcție rulează în fundal și procesează toate mesajele
        primite de la serverul WhatsApp.
        """
        try:
            while self.is_connected and self._websocket:
                try:
                    # Primire mesaj
                    message = await asyncio.wait_for(
                        self._websocket.recv(),
                        timeout=CONNECTION_TIMEOUT
                    )

                    # Actualizare timestamp activitate
                    self.last_activity = time.time()

                    # Procesare mesaj
                    await self._process_message(message)

                except asyncio.TimeoutError:
                    logger.warning(f"[{self.connection_id}] Timeout la așteptarea mesajului. Se verifică conexiunea...")

                    # Verifică dacă websocket-ul este încă deschis
                    if self._websocket and self._websocket.open:
                        continue
                    else:
                        logger.error(f"[{self.connection_id}] Conexiune pierdută")
                        self.is_connected = False
                        break

                except ConnectionClosed as e:
                    logger.error(f"[{self.connection_id}] Conexiune închisă de server: {str(e)}")
                    self.is_connected = False
                    break

                except Exception as e:
                    logger.error(f"[{self.connection_id}] Eroare la procesarea mesajelor: {str(e)}")

            logger.info(f"[{self.connection_id}] Handler mesaje oprit")

        except asyncio.CancelledError:
            # Task anulat, se iese din buclă
            logger.debug(f"[{self.connection_id}] Handler mesaje oprit prin anulare")
        except Exception as e:
            logger.error(f"[{self.connection_id}] Eroare în handler-ul de mesaje: {str(e)}")
            await self._handle_connection_failure(e)

    async def send_message(self, message: Union[Dict[str, Any], bytes, str]) -> bool:
        """
        Trimite un mesaj către serverul WhatsApp.

        Args:
            message: Mesajul de trimis (dict, bytes sau string)

        Returns:
            bool: True dacă mesajul a fost trimis cu succes

        Raises:
            ConnectionError: Dacă nu există o conexiune activă
        """
        if not self.is_connected or not self._websocket:
            raise ConnectionError("Not connected to WhatsApp server")

        try:
            # Determină tipul de mesaj și codifică corespunzător
            if isinstance(message, dict):
                # Mesaj JSON
                encoded = self.protocol.create_json_message_binary(message)
                message_type = "JSON"
            elif isinstance(message, bytes):
                # Mesaj binar deja codificat
                encoded = message
                message_type = "binary"
            elif isinstance(message, str):
                # Mesaj text
                encoded = message.encode('utf-8')
                message_type = "text"
            else:
                raise ValueError(f"Unsupported message type: {type(message)}")

            # Trimite mesajul
            await self._websocket.send(encoded)

            # Actualizare timestamp activitate
            self.last_activity = time.time()

            logger.debug(f"[{self.connection_id}] Mesaj {message_type} trimis")

            # Adaugă mesajul la log dacă este în format JSON
            if isinstance(message, dict):
                log_message = json.dumps(message)[:200]
                if len(log_message) >= 200:
                    log_message += "..."
                logger.debug(f"[{self.connection_id}] Conținut mesaj: {log_message}")

            return True

        except Exception as e:
            logger.error(f"[{self.connection_id}] Eroare la trimiterea mesajului: {str(e)}")

            # Verifică dacă conexiunea este încă deschisă
            if isinstance(e, ConnectionClosed):
                self.is_connected = False
                self.connection_state = CONN_STATE_ERROR

            raise ConnectionError(f"Failed to send message: {str(e)}")

    async def send_handshake(self) -> bool:
        """
        Trimite mesajul de handshake pentru inițierea conexiunii.

        Returns:
            bool: True dacă handshake-ul a fost trimis cu succes
        """
        try:
            # Creează și trimite mesajul de handshake
            handshake_binary = self.protocol.create_handshake_binary()

            logger.info(f"[{self.connection_id}] Trimitere handshake...")
            await self.send_message(handshake_binary)

            # Așteaptă un scurt timp pentru a primi răspunsul
            await asyncio.sleep(1)

            return True

        except Exception as e:
            logger.error(f"[{self.connection_id}] Eroare la trimiterea handshake: {str(e)}")
            return False

    async def _process_message(self, message: Union[bytes, str]) -> None:
        """
        Procesează un mesaj primit de la server.

        Args:
            message: Mesajul primit (bytes sau string)
        """
        try:
            # Determină tipul de mesaj
            is_binary = isinstance(message, bytes)

            if is_binary:
                # Procesează mesaj binar
                try:
                    # Decodifică mesajul binar
                    message_type, decoded_data = self.protocol.process_message(message)

                    # Verifică dacă este un challenge de autentificare
                    if message_type == BINARY_TYPE_CHALLENGE:
                        logger.info(f"[{self.connection_id}] Challenge de autentificare primit")

                        if self._challenge_callback:
                            await self._challenge_callback(decoded_data)
                        else:
                            logger.warning(f"[{self.connection_id}] Challenge primit dar nu există callback")

                    # Handle based on message type (convert to string for type safety)
                    message_type_str = str(message_type) if message_type is not None else "unknown"
                    await self._handle_message_by_type(message_type_str, decoded_data)

                except Exception as e:
                    logger.error(f"[{self.connection_id}] Eroare la decodarea mesajului binar: {str(e)}")

                    # Try fallback text interpretation
                    if message.startswith(b'"'):
                        # Looks like a JSON string
                        try:
                            text_message = message.decode('utf-8')
                            decoded = json.loads(text_message)
                            logger.info(f"[{self.connection_id}] Decodare alternativă reușită: {text_message[:100]}")

                            # Determine and handle message type
                            message_type = self._determine_message_type(decoded)
                            await self._handle_message_by_type(message_type, decoded)

                        except Exception:
                            logger.error(f"[{self.connection_id}] Decodare alternativă eșuată")
            else:
                # Handle text message (likely JSON)
                try:
                    decoded = json.loads(message)

                    # Determine and handle message type
                    message_type = self._determine_message_type(decoded)
                    await self._handle_message_by_type(message_type, decoded)

                except json.JSONDecodeError:
                    logger.warning(f"[{self.connection_id}] Mesaj text non-JSON primit: {message[:100]}")

        except Exception as e:
            logger.error(f"[{self.connection_id}] Eroare la procesarea mesajului: {str(e)}")

    def _determine_message_type(self, data: Any) -> str:
        """
        Determine the type of a received message.

        Args:
            data: Message data

        Returns:
            str: Message type
        """
        if isinstance(data, dict):
            # Check for explicit type field
            if "type" in data:
                return data["type"]

            # Check for common message patterns
            if "message" in data:
                return "chat_message"
            elif "presence" in data:
                return "presence"
            elif "receipt" in data:
                return "receipt"
            elif "status" in data:
                return "status"

        return "unknown"

    async def _handle_message_by_type(self, message_type: str, data: Any) -> None:
        """
        Handle a message based on its type.

        Args:
            message_type: Type of message
            data: Message data
        """
        # Call registered callback for this message type if available
        callback = self._message_callbacks.get(message_type)
        if callback:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"[{self.connection_id}] Eroare în callback pentru mesaj {message_type}: {str(e)}")
        else:
            logger.debug(f"[{self.connection_id}] Niciun callback pentru mesaj de tip {message_type}")

        # Handle some message types specially
        if message_type == "Conn":
            # Connection status update
            if isinstance(data, dict) and data.get("status") == 200:
                logger.info(f"[{self.connection_id}] Conexiune confirmată de server")

                # Save server token if provided
                if "serverToken" in data:
                    self.server_token = data["serverToken"]
                    self.protocol.server_token = self.server_token

    async def _handle_challenge(self, challenge_data: Any) -> None:
        """
        Handle an authentication challenge from the server.

        Args:
            challenge_data: Challenge data
        """
        logger.info(f"[{self.connection_id}] Challenge de autentificare primit")

        # Call challenge callback if registered
        if self._challenge_callback:
            await self._challenge_callback(challenge_data)

    async def _handle_connection_failure(self, exception: Exception) -> None:
        """
        Handle a connection failure.

        Args:
            exception: Exception that caused the failure
        """
        # Log the error
        logger.error(f"[{self.connection_id}] Eroare de conexiune: {str(exception)}")

        # Set connection state
        self.connection_state = CONN_STATE_ERROR
        self.is_connected = False

        # Clean up resources
        if self._websocket:
            try:
                await self._websocket.close()
            except:
                pass
            finally:
                self._websocket = None

    def register_callback(self, message_type: str, callback: Callable) -> None:
        """
        Register a callback for a specific message type.

        Args:
            message_type: Type of message to register callback for
            callback: Callback function to call when message is received
        """
        self._message_callbacks[message_type] = callback

    def register_challenge_callback(self, callback: Callable) -> None:
        """
        Register a callback for processing authentication challenges.

        Args:
            callback: Callback function to process challenge
        """
        self._challenge_callback = callback