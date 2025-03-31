"""
Layer interface for the protocol stack.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Callable, Union

logger = logging.getLogger(__name__)

class Layer:
    """
    Base class for all layers in the protocol stack.
    
    This class defines the interface that all protocol layers must implement,
    including methods for sending and receiving messages between adjacent layers.
    """
    
    def __init__(self, name: str):
        """
        Initialize a protocol layer.
        
        Args:
            name: Name of the layer for identification
        """
        self.name = name
        self.upper = None  # Layer above this one
        self.lower = None  # Layer below this one
        self.event_handlers = {}  # Event handlers for this layer
        
    def set_upper(self, upper: 'Layer') -> None:
        """
        Set the layer above this one in the protocol stack.
        
        Args:
            upper: Layer to set as the upper layer
        """
        self.upper = upper
        
    def set_lower(self, lower: 'Layer') -> None:
        """
        Set the layer below this one in the protocol stack.
        
        Args:
            lower: Layer to set as the lower layer
        """
        self.lower = lower
        
    async def send_to_upper(self, data: Any) -> None:
        """
        Send data to the layer above this one.
        
        Args:
            data: Data to send up the stack
        """
        if self.upper:
            await self.upper.receive_from_lower(data)
        else:
            logger.warning(f"Layer {self.name} has no upper layer to send to")
            
    async def send_to_lower(self, data: Any) -> None:
        """
        Send data to the layer below this one.
        
        Args:
            data: Data to send down the stack
        """
        if self.lower:
            await self.lower.receive_from_upper(data)
        else:
            logger.warning(f"Layer {self.name} has no lower layer to send to")
            
    async def receive_from_upper(self, data: Any) -> None:
        """
        Receive data from the layer above this one.
        
        Args:
            data: Data received from above
        """
        # Default implementation just passes data down
        # Subclasses should override this to process the data
        await self.send_to_lower(data)
        
    async def receive_from_lower(self, data: Any) -> None:
        """
        Receive data from the layer below this one.
        
        Args:
            data: Data received from below
        """
        # Default implementation just passes data up
        # Subclasses should override this to process the data
        await self.send_to_upper(data)
        
    def notify_upper(self, event: Any) -> None:
        """
        Notify the upper layer of an event (non-blocking).
        
        Args:
            event: Event data to notify
        """
        if not self.upper:
            logger.warning(f"Layer {self.name} has no upper layer to notify")
            return
            
        # Create a task to send the event asynchronously
        asyncio.create_task(self.send_to_upper(event))
        
    def notify_lower(self, event: Any) -> None:
        """
        Notify the lower layer of an event (non-blocking).
        
        Args:
            event: Event data to notify
        """
        if not self.lower:
            logger.warning(f"Layer {self.name} has no lower layer to notify")
            return
            
        # Create a task to send the event asynchronously
        asyncio.create_task(self.send_to_lower(event))
        
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Callback function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
            
        self.event_handlers[event_type].append(handler)
        
    def trigger_event(self, event_type: str, event_data: Any = None) -> None:
        """
        Trigger an event and call all registered handlers.
        
        Args:
            event_type: Type of event to trigger
            event_data: Data associated with the event
        """
        if event_type not in self.event_handlers:
            return
            
        for handler in self.event_handlers[event_type]:
            try:
                # Create a task for each handler to run asynchronously
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event_data))
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {str(e)}")
                
    async def handle_event(self, event_type: str, event_data: Any = None) -> None:
        """
        Handle an event synchronously.
        
        Args:
            event_type: Type of event to handle
            event_data: Data associated with the event
        """
        if event_type not in self.event_handlers:
            return
            
        for handler in self.event_handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {str(e)}")
                
    def remove_event_handler(self, event_type: str, handler: Optional[Callable] = None) -> None:
        """
        Remove an event handler.
        
        Args:
            event_type: Type of event
            handler: Handler to remove (if None, remove all for this event type)
        """
        if event_type not in self.event_handlers:
            return
            
        if handler is None:
            # Remove all handlers for this event type
            self.event_handlers[event_type] = []
        else:
            # Remove the specific handler
            self.event_handlers[event_type] = [
                h for h in self.event_handlers[event_type] if h != handler
            ]
            
    async def on_start(self) -> None:
        """
        Called when the layer is started.
        
        Subclasses should override this to perform initialization.
        """
        pass
        
    async def on_stop(self) -> None:
        """
        Called when the layer is stopped.
        
        Subclasses should override this to perform cleanup.
        """
        pass
