"""
Layer interface for WhatsApp protocol stack.

This module defines the interface that all protocol layers must implement,
providing a common API for interaction between layers.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union

logger = logging.getLogger(__name__)

class LayerInterface:
    """
    Interface for protocol layers.
    
    This class defines the interface that all protocol layers must implement,
    including methods to receive data from above and below, and to send data
    up and down the protocol stack.
    """
    
    def __init__(self, name: str):
        """
        Initialize a layer interface.
        
        Args:
            name: Name of the layer
        """
        self.name = name
        self.upper = None  # Layer above this one
        self.lower = None  # Layer below this one
        self.event_listeners = {}
        
    def set_upper(self, upper: 'LayerInterface') -> None:
        """
        Set the layer above this one.
        
        Args:
            upper: Layer above this one
        """
        self.upper = upper
        
    def set_lower(self, lower: 'LayerInterface') -> None:
        """
        Set the layer below this one.
        
        Args:
            lower: Layer below this one
        """
        self.lower = lower
        
    async def send_to_upper(self, data: Any) -> None:
        """
        Send data to the layer above.
        
        Args:
            data: Data to send upward
        """
        if self.upper:
            await self.upper.receive_from_lower(data)
        else:
            logger.warning(f"Layer {self.name} has no upper layer to send data to")
            
    async def send_to_lower(self, data: Any) -> None:
        """
        Send data to the layer below.
        
        Args:
            data: Data to send downward
        """
        if self.lower:
            await self.lower.receive_from_upper(data)
        else:
            logger.warning(f"Layer {self.name} has no lower layer to send data to")
            
    async def receive_from_upper(self, data: Any) -> None:
        """
        Receive data from the layer above.
        
        Args:
            data: Data received from above
        """
        # Default implementation just passes data down
        # Subclasses should override this
        await self.send_to_lower(data)
        
    async def receive_from_lower(self, data: Any) -> None:
        """
        Receive data from the layer below.
        
        Args:
            data: Data received from below
        """
        # Default implementation just passes data up
        # Subclasses should override this
        await self.send_to_upper(data)
        
    def add_event_listener(self, event_type: str, listener: Callable[[Any], None]) -> None:
        """
        Add an event listener.
        
        Args:
            event_type: Type of event to listen for
            listener: Callback function for the event
        """
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
            
        self.event_listeners[event_type].append(listener)
        
    def remove_event_listener(self, event_type: str, listener: Callable[[Any], None]) -> bool:
        """
        Remove an event listener.
        
        Args:
            event_type: Type of event
            listener: Callback function to remove
            
        Returns:
            True if the listener was removed, False if not found
        """
        if event_type not in self.event_listeners:
            return False
            
        if listener in self.event_listeners[event_type]:
            self.event_listeners[event_type].remove(listener)
            return True
            
        return False
        
    def emit_event(self, event_type: str, event_data: Any) -> None:
        """
        Emit an event to all listeners.
        
        Args:
            event_type: Type of event
            event_data: Data for the event
        """
        if event_type not in self.event_listeners:
            return
            
        for listener in self.event_listeners[event_type]:
            try:
                if asyncio.iscoroutinefunction(listener):
                    # Create task for async listeners
                    asyncio.create_task(listener(event_data))
                else:
                    # Call sync listeners directly
                    listener(event_data)
            except Exception as e:
                logger.error(f"Error in event listener for {event_type}: {str(e)}")
                
    async def on_start(self) -> None:
        """
        Called when the layer is started.
        
        Subclasses should override this method to perform initialization.
        """
        pass
        
    async def on_stop(self) -> None:
        """
        Called when the layer is stopped.
        
        Subclasses should override this method to perform cleanup.
        """
        pass
