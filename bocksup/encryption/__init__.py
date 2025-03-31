"""
Modul de criptare pentru Bocksup.

Acest modul implementează criptarea end-to-end folosită de WhatsApp,
bazată pe protocolul Signal (anterior cunoscut ca Axolotl).
"""

from bocksup.encryption.crypto import AESCipher
from bocksup.encryption.signal_protocol import SignalProtocol

__all__ = ["AESCipher", "SignalProtocol"]