"""
Protocol message definitions for WhatsApp.
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class MessageTypes(Enum):
    """
    Enumeration of WhatsApp protocol message types.
    """
    HANDSHAKE = 'handshake'
    AUTH = 'auth'
    LOGIN = 'login'
    HELLO = 'hello'
    GOODBYE = 'goodbye'
    PING = 'ping'
    PONG = 'pong'
    ACK = 'ack'
    CHAT = 'chat'
    GROUP = 'group'
    CONTACT = 'contact'
    MEDIA = 'media'
    PRESENCE = 'presence'
    NOTIFICATION = 'notification'
    STATUS = 'status'
    COMMAND = 'command'
    RECEIPT = 'receipt'
    ERROR = 'error'
    UNKNOWN = 'unknown'

class ProtocolMessage:
    """
    Base class for WhatsApp protocol messages.
    """
    
    def __init__(self, message_type: MessageTypes, tag: Optional[str] = None):
        """
        Initialize a protocol message.
        
        Args:
            message_type: Type of the message
            tag: Optional message tag for correlation
        """
        self.type = message_type
        self.tag = tag or self._generate_tag()
        
    def _generate_tag(self) -> str:
        """
        Generate a unique tag for the message.
        
        Returns:
            A unique tag string
        """
        import uuid
        return str(uuid.uuid4())[:8]
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            'type': self.type.value,
            'tag': self.tag
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolMessage':
        """
        Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A ProtocolMessage instance
        """
        message_type = MessageTypes(data.get('type', 'unknown'))
        tag = data.get('tag')
        
        return cls(message_type, tag)

class HandshakeMessage(ProtocolMessage):
    """
    Handshake message for connection initialization.
    """
    
    def __init__(self, 
                 client_version: str, 
                 features: List[str], 
                 tag: Optional[str] = None):
        """
        Initialize a handshake message.
        
        Args:
            client_version: Client version string
            features: List of supported features
            tag: Optional message tag
        """
        super().__init__(MessageTypes.HANDSHAKE, tag)
        self.client_version = client_version
        self.features = features
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the handshake message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'client_version': self.client_version,
            'features': self.features
        })
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HandshakeMessage':
        """
        Create a handshake message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A HandshakeMessage instance
        """
        return cls(
            data.get('client_version', ''),
            data.get('features', []),
            data.get('tag')
        )

class AuthMessage(ProtocolMessage):
    """
    Authentication message for login.
    """
    
    def __init__(self, 
                 phone: str, 
                 auth_token: str, 
                 client_token: Optional[str] = None,
                 device_id: Optional[str] = None,
                 tag: Optional[str] = None):
        """
        Initialize an authentication message.
        
        Args:
            phone: Phone number
            auth_token: Authentication token
            client_token: Client token (if available)
            device_id: Device identifier
            tag: Optional message tag
        """
        super().__init__(MessageTypes.AUTH, tag)
        self.phone = phone
        self.auth_token = auth_token
        self.client_token = client_token
        self.device_id = device_id
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the authentication message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'phone': self.phone,
            'auth_token': self.auth_token
        })
        
        if self.client_token:
            data['client_token'] = self.client_token
            
        if self.device_id:
            data['device_id'] = self.device_id
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthMessage':
        """
        Create an authentication message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            An AuthMessage instance
        """
        return cls(
            data.get('phone', ''),
            data.get('auth_token', ''),
            data.get('client_token'),
            data.get('device_id'),
            data.get('tag')
        )

class ChatMessage(ProtocolMessage):
    """
    Chat message for text communication.
    """
    
    def __init__(self, 
                 to: str, 
                 body: str, 
                 message_id: Optional[str] = None,
                 quoted_message_id: Optional[str] = None,
                 tag: Optional[str] = None):
        """
        Initialize a chat message.
        
        Args:
            to: Recipient JID
            body: Message text content
            message_id: Unique message ID
            quoted_message_id: ID of message being quoted/replied to
            tag: Optional message tag
        """
        super().__init__(MessageTypes.CHAT, tag)
        self.to = to
        self.body = body
        self.message_id = message_id or self._generate_message_id()
        self.quoted_message_id = quoted_message_id
        
    def _generate_message_id(self) -> str:
        """
        Generate a unique message ID.
        
        Returns:
            A unique message ID string
        """
        import uuid
        prefix = "3EB0"  # WhatsApp-like prefix
        suffix = str(uuid.uuid4()).upper()[4:]
        return f"{prefix}{suffix}"
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the chat message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'to': self.to,
            'body': self.body,
            'message_id': self.message_id
        })
        
        if self.quoted_message_id:
            data['quoted_message_id'] = self.quoted_message_id
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """
        Create a chat message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A ChatMessage instance
        """
        return cls(
            data.get('to', ''),
            data.get('body', ''),
            data.get('message_id'),
            data.get('quoted_message_id'),
            data.get('tag')
        )

class MediaMessage(ProtocolMessage):
    """
    Media message for sending images, audio, video, etc.
    """
    
    def __init__(self, 
                 to: str, 
                 media_type: str, 
                 url: Optional[str] = None,
                 mime_type: Optional[str] = None,
                 filename: Optional[str] = None,
                 size: Optional[int] = None,
                 caption: Optional[str] = None,
                 message_id: Optional[str] = None,
                 tag: Optional[str] = None):
        """
        Initialize a media message.
        
        Args:
            to: Recipient JID
            media_type: Type of media (image, video, audio, document)
            url: URL to the media
            mime_type: MIME type of the media
            filename: Filename of the media
            size: Size of the media in bytes
            caption: Optional caption for the media
            message_id: Unique message ID
            tag: Optional message tag
        """
        super().__init__(MessageTypes.MEDIA, tag)
        self.to = to
        self.media_type = media_type
        self.url = url
        self.mime_type = mime_type
        self.filename = filename
        self.size = size
        self.caption = caption
        self.message_id = message_id or self._generate_message_id()
        
    def _generate_message_id(self) -> str:
        """
        Generate a unique message ID.
        
        Returns:
            A unique message ID string
        """
        import uuid
        prefix = "3EB0"  # WhatsApp-like prefix
        suffix = str(uuid.uuid4()).upper()[4:]
        return f"{prefix}{suffix}"
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the media message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'to': self.to,
            'media_type': self.media_type,
            'message_id': self.message_id
        })
        
        if self.url:
            data['url'] = self.url
            
        if self.mime_type:
            data['mime_type'] = self.mime_type
            
        if self.filename:
            data['filename'] = self.filename
            
        if self.size is not None:
            data['size'] = self.size
            
        if self.caption:
            data['caption'] = self.caption
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaMessage':
        """
        Create a media message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A MediaMessage instance
        """
        return cls(
            data.get('to', ''),
            data.get('media_type', ''),
            data.get('url'),
            data.get('mime_type'),
            data.get('filename'),
            data.get('size'),
            data.get('caption'),
            data.get('message_id'),
            data.get('tag')
        )

class GroupMessage(ProtocolMessage):
    """
    Group management message.
    """
    
    def __init__(self, 
                 group_id: str, 
                 action: str, 
                 participants: Optional[List[str]] = None,
                 subject: Optional[str] = None,
                 tag: Optional[str] = None):
        """
        Initialize a group message.
        
        Args:
            group_id: Group JID
            action: Group action (create, add, remove, leave, subject)
            participants: List of participant JIDs
            subject: Group subject/name
            tag: Optional message tag
        """
        super().__init__(MessageTypes.GROUP, tag)
        self.group_id = group_id
        self.action = action
        self.participants = participants or []
        self.subject = subject
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the group message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'group_id': self.group_id,
            'action': self.action
        })
        
        if self.participants:
            data['participants'] = self.participants
            
        if self.subject:
            data['subject'] = self.subject
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroupMessage':
        """
        Create a group message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A GroupMessage instance
        """
        return cls(
            data.get('group_id', ''),
            data.get('action', ''),
            data.get('participants'),
            data.get('subject'),
            data.get('tag')
        )

class PresenceMessage(ProtocolMessage):
    """
    Presence status message.
    """
    
    def __init__(self, 
                 status: str, 
                 to: Optional[str] = None,
                 tag: Optional[str] = None):
        """
        Initialize a presence message.
        
        Args:
            status: Presence status (available, unavailable, composing, etc.)
            to: Optional recipient JID
            tag: Optional message tag
        """
        super().__init__(MessageTypes.PRESENCE, tag)
        self.status = status
        self.to = to
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the presence message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'status': self.status
        })
        
        if self.to:
            data['to'] = self.to
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PresenceMessage':
        """
        Create a presence message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A PresenceMessage instance
        """
        return cls(
            data.get('status', ''),
            data.get('to'),
            data.get('tag')
        )

class ReceiptMessage(ProtocolMessage):
    """
    Message receipt acknowledgement.
    """
    
    def __init__(self, 
                 message_id: str, 
                 receipt_type: str, 
                 to: Optional[str] = None,
                 tag: Optional[str] = None):
        """
        Initialize a receipt message.
        
        Args:
            message_id: ID of the message being acknowledged
            receipt_type: Type of receipt (received, read, played)
            to: Optional recipient JID
            tag: Optional message tag
        """
        super().__init__(MessageTypes.RECEIPT, tag)
        self.message_id = message_id
        self.receipt_type = receipt_type
        self.to = to
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the receipt message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'message_id': self.message_id,
            'receipt_type': self.receipt_type
        })
        
        if self.to:
            data['to'] = self.to
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceiptMessage':
        """
        Create a receipt message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A ReceiptMessage instance
        """
        return cls(
            data.get('message_id', ''),
            data.get('receipt_type', ''),
            data.get('to'),
            data.get('tag')
        )

class ErrorMessage(ProtocolMessage):
    """
    Error message.
    """
    
    def __init__(self, 
                 code: str, 
                 message: str, 
                 details: Optional[Dict[str, Any]] = None,
                 tag: Optional[str] = None):
        """
        Initialize an error message.
        
        Args:
            code: Error code
            message: Error message
            details: Additional error details
            tag: Optional message tag
        """
        super().__init__(MessageTypes.ERROR, tag)
        self.code = code
        self.message = message
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'code': self.code,
            'message': self.message
        })
        
        if self.details:
            data['details'] = self.details
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorMessage':
        """
        Create an error message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            An ErrorMessage instance
        """
        return cls(
            data.get('code', ''),
            data.get('message', ''),
            data.get('details'),
            data.get('tag')
        )

# Function to create the appropriate message type from a dictionary
def create_message_from_dict(data: Dict[str, Any]) -> ProtocolMessage:
    """
    Create a message of the appropriate type from a dictionary.
    
    Args:
        data: Dictionary representation of the message
        
    Returns:
        A ProtocolMessage instance of the appropriate subclass
    """
    if not isinstance(data, dict):
        logger.warning(f"Invalid message data: {data}")
        return ErrorMessage('invalid_format', 'Message data is not a dictionary')
        
    message_type = data.get('type', 'unknown')
    
    try:
        message_type_enum = MessageTypes(message_type)
    except ValueError:
        logger.warning(f"Unknown message type: {message_type}")
        return ErrorMessage('unknown_type', f"Unknown message type: {message_type}")
        
    # Create the appropriate message type
    if message_type_enum == MessageTypes.HANDSHAKE:
        return HandshakeMessage.from_dict(data)
    elif message_type_enum == MessageTypes.AUTH:
        return AuthMessage.from_dict(data)
    elif message_type_enum == MessageTypes.CHAT:
        return ChatMessage.from_dict(data)
    elif message_type_enum == MessageTypes.MEDIA:
        return MediaMessage.from_dict(data)
    elif message_type_enum == MessageTypes.GROUP:
        return GroupMessage.from_dict(data)
    elif message_type_enum == MessageTypes.PRESENCE:
        return PresenceMessage.from_dict(data)
    elif message_type_enum == MessageTypes.RECEIPT:
        return ReceiptMessage.from_dict(data)
    elif message_type_enum == MessageTypes.ERROR:
        return ErrorMessage.from_dict(data)
    else:
        # For unhandled message types, return a base ProtocolMessage
        return ProtocolMessage(message_type_enum, data.get('tag'))
