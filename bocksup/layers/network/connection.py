"""
Network connection management for WhatsApp servers.
"""

import logging
import asyncio
import ssl
import time
import json
from typing import Optional, Callable, Dict, Any, Union, List, Tuple

import aiohttp
import websockets
from websockets.exceptions import WebSocketException

from bocksup.common.exceptions import ConnectionError, TimeoutError
from bocksup.common.constants import (
    WHATSAPP_SERVER,
    WHATSAPP_PORT,
    WHATSAPP_WEBSOCKET_URL,
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
    PING_INTERVAL
)
from bocksup.layers.interface.layer import Layer

logger = logging.getLogger(__name__)

class Connection(Layer):
    """
    Manages the network connection to WhatsApp servers.
    
    This layer handles the low-level details of establishing and maintaining
    a connection to WhatsApp servers, including reconnection logic and
    heartbeat messages.
    """
    
    def __init__(self, use_websocket: bool = True):
        """
        Initialize the connection layer.
        
        Args:
            use_websocket: Whether to use WebSocket connection (True) or TCP (False)
        """
        super().__init__("NetworkLayer")
        self.use_websocket = use_websocket
        self.connected = False
        self.socket = None
        self.websocket = None
        self.reader = None
        self.writer = None
        self.connect_timeout = CONNECT_TIMEOUT
        self.read_timeout = READ_TIMEOUT
        self.ping_interval = PING_INTERVAL
        self.ping_task = None
        self.read_task = None
        self.last_activity = 0
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5  # seconds
        self._custom_headers = {}
        
    async def connect(self) -> bool:
        """
        Establish a connection to the WhatsApp server.
        
        Returns:
            bool: True if connection was successful
            
        Raises:
            ConnectionError: If connection fails
        """
        if self.connected:
            logger.debug("Already connected, disconnecting first")
            await self.disconnect()
            
        logger.info(f"Connecting to WhatsApp server using {'WebSocket' if self.use_websocket else 'TCP'}")
        
        try:
            if self.use_websocket:
                await self._connect_websocket()
            else:
                await self._connect_tcp()
                
            self.connected = True
            self.last_activity = time.time()
            self._reconnect_attempts = 0
            
            # Start background tasks
            self._start_ping_task()
            self._start_read_task()
            
            logger.info("Successfully connected to WhatsApp server")
            return True
            
        except (asyncio.TimeoutError, aiohttp.ClientError, WebSocketException, OSError) as e:
            logger.error(f"Failed to connect: {str(e)}")
            await self._handle_connection_failure(e)
            return False
            
    async def _connect_websocket(self):
        """
        Establish a WebSocket connection to WhatsApp.
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Prepare connection headers
            headers = {
                'User-Agent': 'Bocksup/0.1.0',
                'Origin': 'https://web.whatsapp.com'
            }
            headers.update(self._custom_headers)
            
            # Connect with timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    WHATSAPP_WEBSOCKET_URL,
                    extra_headers=headers,
                    ping_interval=None,  # We'll handle pings manually
                    ping_timeout=None,
                    close_timeout=5
                ),
                timeout=self.connect_timeout
            )
            
        except (asyncio.TimeoutError, WebSocketException, OSError) as e:
            raise ConnectionError(f"WebSocket connection failed: {str(e)}")
            
    async def _connect_tcp(self):
        """
        Establish a TCP connection to WhatsApp.
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Create SSL context for secure connection
            ssl_context = ssl.create_default_context()
            
            # Connect with timeout
            connection_task = asyncio.open_connection(
                WHATSAPP_SERVER,
                WHATSAPP_PORT,
                ssl=ssl_context
            )
            
            self.reader, self.writer = await asyncio.wait_for(
                connection_task,
                timeout=self.connect_timeout
            )
            
        except (asyncio.TimeoutError, OSError) as e:
            raise ConnectionError(f"TCP connection failed: {str(e)}")
            
    async def disconnect(self) -> None:
        """
        Disconnect from the WhatsApp server.
        """
        if not self.connected:
            logger.debug("Already disconnected")
            return
            
        logger.info("Disconnecting from WhatsApp server")
        
        # Cancel background tasks
        if self.ping_task and not self.ping_task.done():
            self.ping_task.cancel()
            
        if self.read_task and not self.read_task.done():
            self.read_task.cancel()
            
        try:
            # Close WebSocket connection
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
                
            # Close TCP connection
            if self.writer:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except Exception:
                    pass
                self.writer = None
                self.reader = None
                
        except Exception as e:
            logger.warning(f"Error during disconnect: {str(e)}")
            
        finally:
            self.connected = False
            
    async def send(self, data: Union[bytes, str, Dict[str, Any]]) -> bool:
        """
        Send data to the WhatsApp server.
        
        Args:
            data: Data to send (bytes, string, or dict that will be JSON-encoded)
            
        Returns:
            bool: True if send was successful
            
        Raises:
            ConnectionError: If send fails or not connected
        """
        if not self.connected:
            raise ConnectionError("Not connected to WhatsApp server")
            
        try:
            # Convert data to appropriate format
            if isinstance(data, dict):
                data = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                data = data.encode('utf-8')
                
            # Send data based on connection type
            if self.use_websocket:
                await self.websocket.send(data)
            else:
                self.writer.write(data)
                await self.writer.drain()
                
            self.last_activity = time.time()
            return True
            
        except (WebSocketException, OSError, asyncio.CancelledError) as e:
            logger.error(f"Error sending data: {str(e)}")
            await self._handle_connection_failure(e)
            return False
            
    async def receive(self, timeout: Optional[float] = None) -> bytes:
        """
        Receive data from the WhatsApp server.
        
        Args:
            timeout: Timeout in seconds (None for default)
            
        Returns:
            bytes: Received data
            
        Raises:
            ConnectionError: If receive fails or not connected
            TimeoutError: If receive times out
        """
        if not self.connected:
            raise ConnectionError("Not connected to WhatsApp server")
            
        timeout = timeout or self.read_timeout
        
        try:
            # Receive data based on connection type
            if self.use_websocket:
                data = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=timeout
                )
                
                # Convert string to bytes if necessary
                if isinstance(data, str):
                    data = data.encode('utf-8')
                    
            else:
                data = await asyncio.wait_for(
                    self.reader.read(8192),  # Read up to 8KB at a time
                    timeout=timeout
                )
                
                if not data:  # Empty data means the connection was closed
                    raise ConnectionError("Connection closed by server")
                    
            self.last_activity = time.time()
            return data
            
        except asyncio.TimeoutError:
            logger.warning(f"Receive timeout after {timeout} seconds")
            raise TimeoutError(f"Receive timeout after {timeout} seconds")
            
        except (WebSocketException, OSError, asyncio.CancelledError) as e:
            logger.error(f"Error receiving data: {str(e)}")
            await self._handle_connection_failure(e)
            raise ConnectionError(f"Error receiving data: {str(e)}")
            
    def _start_ping_task(self) -> None:
        """
        Start a background task to send periodic pings to keep the connection alive.
        """
        if self.ping_task and not self.ping_task.done():
            self.ping_task.cancel()
            
        self.ping_task = asyncio.create_task(self._ping_loop())
        
    def _start_read_task(self) -> None:
        """
        Start a background task to continuously read from the connection.
        """
        if self.read_task and not self.read_task.done():
            self.read_task.cancel()
            
        self.read_task = asyncio.create_task(self._read_loop())
        
    async def _ping_loop(self) -> None:
        """
        Background task that sends periodic pings to keep the connection alive.
        """
        try:
            while self.connected:
                # Check if we need to send a ping
                time_since_activity = time.time() - self.last_activity
                
                if time_since_activity >= self.ping_interval:
                    logger.debug("Sending ping to keep connection alive")
                    
                    if self.use_websocket:
                        # For WebSockets, use the ping protocol
                        pong_waiter = await self.websocket.ping()
                        await asyncio.wait_for(pong_waiter, timeout=5)
                    else:
                        # For TCP, send an application-level ping
                        ping_data = {'type': 'ping', 'timestamp': int(time.time())}
                        await self.send(ping_data)
                        
                    self.last_activity = time.time()
                    
                # Wait before checking again
                await asyncio.sleep(min(self.ping_interval, 15))
                
        except asyncio.CancelledError:
            logger.debug("Ping task cancelled")
        except Exception as e:
            logger.error(f"Error in ping loop: {str(e)}")
            await self._handle_connection_failure(e)
            
    async def _read_loop(self) -> None:
        """
        Background task that continuously reads from the connection.
        """
        try:
            while self.connected:
                try:
                    data = await self.receive()
                    
                    # Process the received data
                    if data:
                        # Forward data to upper layer
                        self.notify_upper(data)
                        
                except TimeoutError:
                    # Timeout is fine, just continue
                    pass
                    
        except asyncio.CancelledError:
            logger.debug("Read task cancelled")
        except Exception as e:
            logger.error(f"Error in read loop: {str(e)}")
            await self._handle_connection_failure(e)
            
    async def _handle_connection_failure(self, exception: Exception) -> None:
        """
        Handle connection failures, including reconnection logic.
        
        Args:
            exception: The exception that caused the failure
        """
        self.connected = False
        
        # Clean up resources
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None
            
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
            self.writer = None
            self.reader = None
            
        # Attempt to reconnect if configured
        if self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            delay = self._reconnect_delay * self._reconnect_attempts
            
            logger.info(f"Connection lost. Reconnecting in {delay} seconds (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts})")
            
            # Notify upper layers about the disconnection
            self.notify_upper({'event': 'disconnected', 'error': str(exception)})
            
            await asyncio.sleep(delay)
            
            # Attempt to reconnect
            try:
                reconnected = await self.connect()
                if reconnected:
                    # Notify upper layers about the reconnection
                    self.notify_upper({'event': 'reconnected'})
            except Exception as e:
                logger.error(f"Reconnection failed: {str(e)}")
        else:
            logger.error(f"Maximum reconnection attempts reached. Giving up.")
            # Notify upper layers about permanent disconnection
            self.notify_upper({
                'event': 'connection_failed',
                'error': str(exception),
                'permanent': True
            })
            
    def set_header(self, name: str, value: str) -> None:
        """
        Set a custom header for WebSocket connections.
        
        Args:
            name: Header name
            value: Header value
        """
        self._custom_headers[name] = value
        
    def set_connect_timeout(self, timeout: float) -> None:
        """
        Set the connection timeout.
        
        Args:
            timeout: Timeout in seconds
        """
        self.connect_timeout = timeout
        
    def set_read_timeout(self, timeout: float) -> None:
        """
        Set the read timeout.
        
        Args:
            timeout: Timeout in seconds
        """
        self.read_timeout = timeout
        
    def set_ping_interval(self, interval: float) -> None:
        """
        Set the ping interval.
        
        Args:
            interval: Interval in seconds
        """
        self.ping_interval = interval
        
    def set_reconnect_params(self, max_attempts: int, delay: float) -> None:
        """
        Set reconnection parameters.
        
        Args:
            max_attempts: Maximum number of reconnection attempts
            delay: Base delay between attempts (will be multiplied by attempt number)
        """
        self._max_reconnect_attempts = max_attempts
        self._reconnect_delay = delay
        
    def is_connected(self) -> bool:
        """
        Check if the connection is active.
        
        Returns:
            bool: True if connected
        """
        return self.connected
        
    async def reset(self) -> None:
        """
        Reset the connection.
        """
        await self.disconnect()
        self._reconnect_attempts = 0
