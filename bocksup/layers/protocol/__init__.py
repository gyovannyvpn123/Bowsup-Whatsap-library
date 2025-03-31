"""
Pachetul de protocol.

Acest pachet conține clasele care implementează protocolul 
specific WhatsApp, formatele de mesaje și codificările.
"""

from .websocket_protocol import WebSocketProtocol

__all__ = ['WebSocketProtocol']