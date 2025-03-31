"""
Custom exceptions for the Bocksup library.
"""

class BocksupException(Exception):
    """Base exception for all Bocksup-related errors."""
    pass

class AuthenticationError(BocksupException):
    """Raised when authentication with WhatsApp servers fails."""
    pass

class ConnectionError(BocksupException):
    """Raised when a connection to WhatsApp servers cannot be established or is lost."""
    pass

class MessageError(BocksupException):
    """Raised when there is an error sending or receiving a message."""
    pass

class ProtocolError(BocksupException):
    """Raised when there is an error in the WhatsApp protocol."""
    pass

class MediaError(BocksupException):
    """Raised when there is an error processing media files."""
    pass

class EncryptionError(BocksupException):
    """Raised when there is an error with encryption or decryption."""
    pass

class RegistrationError(BocksupException):
    """Raised when there is an error with the registration process."""
    pass

class GroupError(BocksupException):
    """Raised when there is an error with group operations."""
    pass

class ContactError(BocksupException):
    """Raised when there is an error with contact operations."""
    pass

class StatusError(BocksupException):
    """Raised when there is an error with status updates."""
    pass

class TimeoutError(BocksupException):
    """Raised when an operation times out."""
    pass

class ValidationError(BocksupException):
    """Raised when input validation fails."""
    pass

class ParseError(BocksupException):
    """Raised when parsing of incoming data fails."""
    pass

class NotImplementedError(BocksupException):
    """Raised when a required feature is not yet implemented."""
    pass
