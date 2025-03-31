"""
Message handlers for WhatsApp communication.

This module provides handlers for processing messages, including
callbacks for different message types and events.
"""

import logging
import asyncio
import inspect
from typing import Dict, Any, Callable, Optional, List, Union, Tuple, Awaitable

from bocksup.messaging.messages import Message, TextMessage, MediaMessage, LocationMessage, ContactMessage
from bocksup.common.exceptions import MessageError

logger = logging.getLogger(__name__)

# Type for message handlers
MessageHandlerType = Callable[[Message], Union[Awaitable[None], None]]

class MessageHandler:
    """
    Handles and routes incoming messages to appropriate callbacks.
    
    This class manages the registration of callbacks for different message types
    and events, and routes incoming messages to those callbacks.
    """
    
    def __init__(self):
        """
        Initialize the message handler.
        """
        self._handlers = {
            'text': [],
            'media': [],
            'location': [],
            'contact': [],
            'receipt': [],
            'presence': [],
            'any': []  # Handlers for any message type
        }
        
    def register_handler(self, 
                        message_type: str, 
                        handler: MessageHandlerType, 
                        priority: int = 50) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Callback function
            priority: Priority of the handler (lower values get called first)
            
        Raises:
            ValueError: If message_type is not supported
            TypeError: If handler is not callable
        """
        if message_type not in self._handlers:
            raise ValueError(f"Unsupported message type: {message_type}")
            
        if not callable(handler):
            raise TypeError("Handler must be callable")
            
        self._handlers[message_type].append((handler, priority))
        # Sort handlers by priority
        self._handlers[message_type].sort(key=lambda x: x[1])
        
        logger.debug(f"Registered handler for message type '{message_type}' with priority {priority}")
        
    def unregister_handler(self, 
                          message_type: str, 
                          handler: MessageHandlerType) -> bool:
        """
        Unregister a handler for a specific message type.
        
        Args:
            message_type: Type of message
            handler: Callback function to remove
            
        Returns:
            True if handler was found and removed, False otherwise
            
        Raises:
            ValueError: If message_type is not supported
        """
        if message_type not in self._handlers:
            raise ValueError(f"Unsupported message type: {message_type}")
            
        for i, (h, _) in enumerate(self._handlers[message_type]):
            if h == handler:
                del self._handlers[message_type][i]
                logger.debug(f"Unregistered handler for message type '{message_type}'")
                return True
                
        logger.debug(f"Handler for message type '{message_type}' not found")
        return False
        
    def register_text_handler(self, handler: MessageHandlerType, priority: int = 50) -> None:
        """
        Register a handler for text messages.
        
        Args:
            handler: Callback function
            priority: Priority of the handler
        """
        self.register_handler('text', handler, priority)
        
    def register_media_handler(self, handler: MessageHandlerType, priority: int = 50) -> None:
        """
        Register a handler for media messages.
        
        Args:
            handler: Callback function
            priority: Priority of the handler
        """
        self.register_handler('media', handler, priority)
        
    def register_location_handler(self, handler: MessageHandlerType, priority: int = 50) -> None:
        """
        Register a handler for location messages.
        
        Args:
            handler: Callback function
            priority: Priority of the handler
        """
        self.register_handler('location', handler, priority)
        
    def register_contact_handler(self, handler: MessageHandlerType, priority: int = 50) -> None:
        """
        Register a handler for contact messages.
        
        Args:
            handler: Callback function
            priority: Priority of the handler
        """
        self.register_handler('contact', handler, priority)
        
    def register_receipt_handler(self, handler: MessageHandlerType, priority: int = 50) -> None:
        """
        Register a handler for receipt messages.
        
        Args:
            handler: Callback function
            priority: Priority of the handler
        """
        self.register_handler('receipt', handler, priority)
        
    def register_presence_handler(self, handler: MessageHandlerType, priority: int = 50) -> None:
        """
        Register a handler for presence updates.
        
        Args:
            handler: Callback function
            priority: Priority of the handler
        """
        self.register_handler('presence', handler, priority)
        
    def register_any_handler(self, handler: MessageHandlerType, priority: int = 50) -> None:
        """
        Register a handler for any message type.
        
        Args:
            handler: Callback function
            priority: Priority of the handler
        """
        self.register_handler('any', handler, priority)
        
    async def handle_message(self, message: Message) -> None:
        """
        Handle an incoming message.
        
        This method routes the message to the appropriate handlers
        based on its type and executes them in priority order.
        
        Args:
            message: Message to handle
        """
        logger.debug(f"Handling message: {message}")
        
        # Determine message type
        if isinstance(message, TextMessage):
            message_type = 'text'
        elif isinstance(message, MediaMessage):
            message_type = 'media'
        elif isinstance(message, LocationMessage):
            message_type = 'location'
        elif isinstance(message, ContactMessage):
            message_type = 'contact'
        else:
            # Try to get type from dictionary representation
            message_dict = message.to_dict()
            message_type = message_dict.get('type', 'any')
            
        try:
            # First, execute specific handlers for this message type
            if message_type in self._handlers:
                for handler, _ in self._handlers[message_type]:
                    await self._execute_handler(handler, message)
                    
            # Then, execute any-type handlers
            for handler, _ in self._handlers['any']:
                await self._execute_handler(handler, message)
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            
    async def _execute_handler(self, handler: MessageHandlerType, message: Message) -> None:
        """
        Execute a message handler.
        
        This method handles both synchronous and asynchronous handlers.
        
        Args:
            handler: Handler function to execute
            message: Message to pass to the handler
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                # Asynchronous handler
                await handler(message)
            else:
                # Synchronous handler - run in a thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, message)
                
        except Exception as e:
            logger.error(f"Error in message handler: {str(e)}")
            
    def has_handlers(self, message_type: str) -> bool:
        """
        Check if there are any handlers registered for a message type.
        
        Args:
            message_type: Type of message
            
        Returns:
            True if handlers exist, False otherwise
            
        Raises:
            ValueError: If message_type is not supported
        """
        if message_type not in self._handlers:
            raise ValueError(f"Unsupported message type: {message_type}")
            
        return len(self._handlers[message_type]) > 0 or len(self._handlers['any']) > 0
        
    def clear_handlers(self, message_type: Optional[str] = None) -> None:
        """
        Clear all handlers for a specific message type or all types.
        
        Args:
            message_type: Type of message to clear handlers for, or None for all
            
        Raises:
            ValueError: If message_type is not supported
        """
        if message_type is not None:
            if message_type not in self._handlers:
                raise ValueError(f"Unsupported message type: {message_type}")
                
            self._handlers[message_type] = []
            logger.debug(f"Cleared handlers for message type '{message_type}'")
        else:
            # Clear all handlers
            for msg_type in self._handlers:
                self._handlers[msg_type] = []
                
            logger.debug("Cleared all message handlers")
