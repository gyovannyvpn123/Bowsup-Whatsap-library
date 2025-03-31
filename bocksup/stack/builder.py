"""
Stack builder for WhatsApp protocol.

This module provides the functionality to build and configure
the protocol stack for WhatsApp communication.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union, Callable

from bocksup.layers.interface.layer import Layer
from bocksup.layers.network.connection import Connection
from bocksup.layers.protocol.serialization import Serializer
from bocksup.layers.axolotl.layer import AxolotlLayer
from bocksup.auth.authenticator import Authenticator
from bocksup.config.settings import Settings

logger = logging.getLogger(__name__)

class StackBuilder:
    """
    Builds the protocol stack for WhatsApp communication.
    
    This class creates and configures the layers of the WhatsApp protocol stack,
    establishing the connections between them to create a complete communication stack.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the stack builder.
        
        Args:
            settings: Configuration settings (if None, default settings are used)
        """
        self.settings = settings or Settings()
        self.on_message_callback = None
        self.on_receipt_callback = None
        self.on_presence_callback = None
        self.on_group_notification_callback = None
        self.on_disconnect_callback = None
        
    def build(self, 
              credentials: Tuple[str, str], 
              encryption_enabled: bool = True) -> 'WhatsAppStack':
        """
        Build the WhatsApp protocol stack.
        
        Args:
            credentials: Tuple of (phone_number, password)
            encryption_enabled: Whether to enable end-to-end encryption
            
        Returns:
            Configured WhatsAppStack instance
        """
        logger.info("Building WhatsApp protocol stack")
        
        # Extract credentials
        phone_number, password = credentials
        
        # Create the layers
        network_layer = self._create_network_layer()
        auth_layer = self._create_auth_layer(phone_number, password)
        
        # Create stack
        stack = WhatsAppStack(network_layer, auth_layer)
        
        # Add encryption layer if enabled
        if encryption_enabled:
            encryption_layer = self._create_encryption_layer()
            stack.add_layer(encryption_layer)
            
        # Configure layer connections
        self._connect_layers(stack.layers)
        
        # Set up event handlers for the stack
        self._setup_event_handlers(stack)
        
        logger.info("WhatsApp protocol stack built successfully")
        
        return stack
        
    def _create_network_layer(self) -> Connection:
        """
        Create the network layer.
        
        Returns:
            Configured network layer
        """
        use_websocket = self.settings.get('advanced', 'use_websockets', True)
        network_layer = Connection(use_websocket=use_websocket)
        
        # Configure network parameters from settings
        connect_timeout = self.settings.get('connection', 'timeout', 30)
        read_timeout = self.settings.get('connection', 'timeout', 30)
        ping_interval = self.settings.get('connection', 'ping_interval', 60)
        max_retries = self.settings.get('connection', 'max_retries', 5)
        retry_delay = self.settings.get('connection', 'retry_delay', 5)
        
        network_layer.set_connect_timeout(connect_timeout)
        network_layer.set_read_timeout(read_timeout)
        network_layer.set_ping_interval(ping_interval)
        network_layer.set_reconnect_params(max_retries, retry_delay)
        
        return network_layer
        
    def _create_auth_layer(self, phone_number: str, password: str) -> Authenticator:
        """
        Create the authentication layer.
        
        Args:
            phone_number: WhatsApp phone number
            password: WhatsApp password
            
        Returns:
            Configured authentication layer
        """
        return Authenticator(phone_number, password)
        
    def _create_encryption_layer(self) -> AxolotlLayer:
        """
        Create the encryption layer.
        
        Returns:
            Configured encryption layer
        """
        store_path = self.settings.get('encryption', 'key_store_path', './keys')
        return AxolotlLayer(store_path=store_path)
        
    def _connect_layers(self, layers: List[Layer]) -> None:
        """
        Connect the layers in the stack.
        
        This establishes the upper/lower relationships between layers.
        
        Args:
            layers: List of layers to connect
        """
        # Connect each layer to the ones above and below it
        for i in range(len(layers)):
            if i > 0:
                layers[i].set_lower(layers[i-1])
                
            if i < len(layers) - 1:
                layers[i].set_upper(layers[i+1])
                
    def _setup_event_handlers(self, stack: 'WhatsAppStack') -> None:
        """
        Set up event handlers for the stack.
        
        Args:
            stack: WhatsAppStack to set up handlers for
        """
        # Pass the callbacks to the stack
        stack.on_message_callback = self.on_message_callback
        stack.on_receipt_callback = self.on_receipt_callback
        stack.on_presence_callback = self.on_presence_callback
        stack.on_group_notification_callback = self.on_group_notification_callback
        stack.on_disconnect_callback = self.on_disconnect_callback
        
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set the handler for incoming messages.
        
        Args:
            handler: Callback function for messages
        """
        self.on_message_callback = handler
        
    def set_receipt_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set the handler for message receipts.
        
        Args:
            handler: Callback function for receipts
        """
        self.on_receipt_callback = handler
        
    def set_presence_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set the handler for presence updates.
        
        Args:
            handler: Callback function for presence updates
        """
        self.on_presence_callback = handler
        
    def set_group_notification_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set the handler for group notifications.
        
        Args:
            handler: Callback function for group notifications
        """
        self.on_group_notification_callback = handler
        
    def set_disconnect_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set the handler for disconnection events.
        
        Args:
            handler: Callback function for disconnections
        """
        self.on_disconnect_callback = handler

class WhatsAppStack:
    """
    Complete WhatsApp protocol stack.
    
    This class represents the complete stack of protocol layers for WhatsApp communication,
    providing methods to interact with the stack as a whole.
    """
    
    def __init__(self, network_layer: Connection, auth_layer: Authenticator):
        """
        Initialize the WhatsApp stack.
        
        Args:
            network_layer: Network layer for the stack
            auth_layer: Authentication layer for the stack
        """
        self.layers = [network_layer, auth_layer]
        self.network_layer = network_layer
        self.auth_layer = auth_layer
        self.encryption_layer = None
        self.serializer = Serializer()
        
        # Event callbacks
        self.on_message_callback = None
        self.on_receipt_callback = None
        self.on_presence_callback = None
        self.on_group_notification_callback = None
        self.on_disconnect_callback = None
        
        # State
        self.is_connected = False
        self.is_authenticated = False
        
    def add_layer(self, layer: Layer) -> None:
        """
        Add a layer to the stack.
        
        Args:
            layer: Layer to add
        """
        # Store encryption layer for easy access
        if isinstance(layer, AxolotlLayer):
            self.encryption_layer = layer
            
        # Add to layers list
        self.layers.append(layer)
        
    async def connect(self) -> bool:
        """
        Connect to WhatsApp servers.
        
        Returns:
            True if connection was successful
        """
        logger.info("Connecting to WhatsApp servers")
        
        try:
            # Connect network layer
            if not await self.network_layer.connect():
                logger.error("Failed to connect to WhatsApp servers")
                return False
                
            self.is_connected = True
            logger.info("Connected to WhatsApp servers")
            
            # Register event handlers
            self._register_event_handlers()
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to WhatsApp servers: {str(e)}")
            return False
            
    async def disconnect(self) -> None:
        """
        Disconnect from WhatsApp servers.
        """
        logger.info("Disconnecting from WhatsApp servers")
        
        try:
            # Disconnect network layer
            await self.network_layer.disconnect()
            self.is_connected = False
            self.is_authenticated = False
            
            logger.info("Disconnected from WhatsApp servers")
            
        except Exception as e:
            logger.error(f"Error disconnecting from WhatsApp servers: {str(e)}")
            
    async def authenticate(self) -> bool:
        """
        Authenticate with WhatsApp servers.
        
        Returns:
            True if authentication was successful
        """
        logger.info("Authenticating with WhatsApp servers")
        
        try:
            # Check if we're connected
            if not self.is_connected:
                logger.error("Cannot authenticate: Not connected to WhatsApp servers")
                return False
                
            # Authenticate
            if not await self.auth_layer.authenticate():
                logger.error("Authentication failed")
                return False
                
            self.is_authenticated = True
            logger.info("Authentication successful")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return False
            
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send a message through the stack.
        
        Args:
            message: Message to send
            
        Returns:
            True if sending was successful
        """
        logger.debug(f"Sending message: {message.get('type', 'unknown')}")
        
        try:
            # Check if we're connected and authenticated
            if not self.is_connected:
                logger.error("Cannot send message: Not connected to WhatsApp servers")
                return False
                
            if not self.is_authenticated:
                logger.error("Cannot send message: Not authenticated")
                return False
                
            # Serialize the message
            serialize_encryp = self.encryption_layer is not None
            data = self.serializer.serialize(message, encrypt=serialize_encryp)
            
            # Send the message through the network layer
            return await self.network_layer.send(data)
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
            
    def _register_event_handlers(self) -> None:
        """
        Register event handlers for the stack layers.
        """
        # Register handlers for network events
        self.network_layer.register_event_handler('disconnected', self._handle_disconnect)
        self.network_layer.register_event_handler('reconnected', self._handle_reconnect)
        self.network_layer.register_event_handler('connection_failed', self._handle_connection_failed)
        
        # TODO: Register handlers for other events as needed
        
    def _handle_disconnect(self, event_data: Any) -> None:
        """
        Handle disconnection events.
        
        Args:
            event_data: Event data
        """
        logger.info("Handling disconnect event")
        self.is_connected = False
        self.is_authenticated = False
        
        # Trigger callback if set
        if self.on_disconnect_callback:
            self.on_disconnect_callback({
                'type': 'disconnect',
                'error': event_data.get('error') if isinstance(event_data, dict) else None
            })
            
    def _handle_reconnect(self, event_data: Any) -> None:
        """
        Handle reconnection events.
        
        Args:
            event_data: Event data
        """
        logger.info("Handling reconnect event")
        self.is_connected = True
        
        # Attempt to re-authenticate
        asyncio.create_task(self._reauthenticate())
        
    def _handle_connection_failed(self, event_data: Any) -> None:
        """
        Handle connection failure events.
        
        Args:
            event_data: Event data
        """
        logger.error("Handling connection failure event")
        self.is_connected = False
        self.is_authenticated = False
        
        # Trigger callback if set
        if self.on_disconnect_callback:
            self.on_disconnect_callback({
                'type': 'connection_failed',
                'error': event_data.get('error') if isinstance(event_data, dict) else None,
                'permanent': event_data.get('permanent', False) if isinstance(event_data, dict) else False
            })
            
    async def _reauthenticate(self) -> None:
        """
        Re-authenticate after reconnecting.
        """
        logger.info("Re-authenticating after reconnection")
        
        try:
            # Authenticate
            if await self.auth_layer.authenticate():
                logger.info("Re-authentication successful")
                self.is_authenticated = True
            else:
                logger.error("Re-authentication failed")
                
        except Exception as e:
            logger.error(f"Error during re-authentication: {str(e)}")
