"""
Excepții personalizate pentru biblioteca Bocksup.
"""

class BocksupError(Exception):
    """Excepție de bază pentru toate erorile Bocksup."""
    pass

class ConnectionError(BocksupError):
    """Excepție pentru erori de conexiune la serverele WhatsApp."""
    pass

class AuthenticationError(BocksupError):
    """Excepție pentru erori de autentificare."""
    pass

class MessageError(BocksupError):
    """Excepție pentru erori la trimiterea sau primirea mesajelor."""
    pass

class ProtocolError(BocksupError):
    """Excepție pentru erori de protocol (formate greșite, versiuni incompatibile, etc.)."""
    pass

class CryptoError(BocksupError):
    """Excepție pentru erori de criptare sau decriptare."""
    pass

class MediaError(BocksupError):
    """Excepție pentru erori la manipularea fișierelor media."""
    pass