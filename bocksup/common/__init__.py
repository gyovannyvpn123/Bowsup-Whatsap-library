"""
Pachetul comun.

Acest pachet conține elemente comune folosite în întreaga bibliotecă,
precum constante, excepții și utilități generale.
"""

from .exceptions import (
    BocksupError,
    ConnectionError,
    AuthenticationError,
    MessageError,
    ProtocolError,
    CryptoError,
    MediaError
)

__all__ = [
    'BocksupError',
    'ConnectionError',
    'AuthenticationError',
    'MessageError',
    'ProtocolError',
    'CryptoError',
    'MediaError'
]