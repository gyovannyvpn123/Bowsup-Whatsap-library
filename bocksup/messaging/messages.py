"""
Message classes for WhatsApp communication.

This module defines the various types of messages that can be sent and received
through WhatsApp, including text messages, media messages, location messages, etc.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Union, Tuple

from bocksup.common.exceptions import MessageError
from bocksup.common.utils import generate_message_id, phone_to_jid

logger = logging.getLogger(__name__)

class Message:
    """
    Base class for all message types.
    
    This class provides common functionality for all messages,
    including ID generation, timestamp handling, and conversion
    to/from dictionaries for the protocol layer.
    """
    
    def __init__(self, 
                 to: Optional[str] = None,
                 from_jid: Optional[str] = None,
                 id: Optional[str] = None,
                 timestamp: Optional[int] = None,
                 participant: Optional[str] = None,
                 quoted_message_id: Optional[str] = None,
                 quoted_message: Optional[Dict[str, Any]] = None,
                 is_group: bool = False):
        """
        Initialize a message.
        
        Args:
            to: Recipient JID or phone number
            from_jid: Sender JID (usually set by the system for incoming messages)
            id: Message ID (if None, a new one is generated)
            timestamp: Message timestamp (if None, current time is used)
            participant: Group participant who sent the message (for group messages)
            quoted_message_id: ID of message being quoted/replied to
            quoted_message: Content of the quoted message
            is_group: Whether the message is for a group
        """
        # Convert phone number to JID if needed
        if to and '@' not in to:
            to = phone_to_jid(to)
            
        self.to = to
        self.from_jid = from_jid
        self.id = id or generate_message_id()
        self.timestamp = timestamp or int(time.time() * 1000)  # milliseconds
        self.participant = participant
        self.quoted_message_id = quoted_message_id
        self.quoted_message = quoted_message
        self.is_group = is_group
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary for protocol processing.
        
        Returns:
            Dictionary representation of the message
        """
        data = {
            'id': self.id,
            'timestamp': self.timestamp
        }
        
        if self.to:
            data['to'] = self.to
            
        if self.from_jid:
            data['from'] = self.from_jid
            
        if self.participant:
            data['participant'] = self.participant
            
        if self.quoted_message_id:
            data['quoted_message_id'] = self.quoted_message_id
            
        if self.quoted_message:
            data['quoted_message'] = self.quoted_message
            
        if self.is_group:
            data['is_group'] = True
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            Message instance
        """
        return cls(
            to=data.get('to'),
            from_jid=data.get('from'),
            id=data.get('id'),
            timestamp=data.get('timestamp'),
            participant=data.get('participant'),
            quoted_message_id=data.get('quoted_message_id'),
            quoted_message=data.get('quoted_message'),
            is_group=data.get('is_group', False)
        )
        
    def __repr__(self) -> str:
        """
        String representation of the message.
        
        Returns:
            String representation
        """
        return f"<{self.__class__.__name__} id={self.id} to={self.to} from={self.from_jid}>"

class TextMessage(Message):
    """
    Text message for WhatsApp.
    """
    
    def __init__(self, 
                 body: str, 
                 to: Optional[str] = None,
                 from_jid: Optional[str] = None,
                 id: Optional[str] = None,
                 timestamp: Optional[int] = None,
                 participant: Optional[str] = None,
                 quoted_message_id: Optional[str] = None,
                 quoted_message: Optional[Dict[str, Any]] = None,
                 is_group: bool = False,
                 mentions: Optional[List[str]] = None,
                 formatting: Optional[Dict[str, Any]] = None):
        """
        Initialize a text message.
        
        Args:
            body: Text content of the message
            to: Recipient JID or phone number
            from_jid: Sender JID
            id: Message ID
            timestamp: Message timestamp
            participant: Group participant who sent the message
            quoted_message_id: ID of message being quoted/replied to
            quoted_message: Content of the quoted message
            is_group: Whether the message is for a group
            mentions: List of JIDs mentioned in the message
            formatting: Formatting metadata (bold, italic, etc.)
        """
        super().__init__(
            to=to,
            from_jid=from_jid,
            id=id,
            timestamp=timestamp,
            participant=participant,
            quoted_message_id=quoted_message_id,
            quoted_message=quoted_message,
            is_group=is_group
        )
        self.body = body
        self.mentions = mentions or []
        self.formatting = formatting or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the text message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'type': 'text',
            'body': self.body
        })
        
        if self.mentions:
            data['mentions'] = self.mentions
            
        if self.formatting:
            data['formatting'] = self.formatting
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextMessage':
        """
        Create a text message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            TextMessage instance
        """
        return cls(
            body=data.get('body', ''),
            to=data.get('to'),
            from_jid=data.get('from'),
            id=data.get('id'),
            timestamp=data.get('timestamp'),
            participant=data.get('participant'),
            quoted_message_id=data.get('quoted_message_id'),
            quoted_message=data.get('quoted_message'),
            is_group=data.get('is_group', False),
            mentions=data.get('mentions'),
            formatting=data.get('formatting')
        )
        
    def __repr__(self) -> str:
        """
        String representation of the text message.
        
        Returns:
            String representation
        """
        return f"<TextMessage id={self.id} body=\"{self.body[:20]}{'...' if len(self.body) > 20 else ''}\">"

class MediaMessage(Message):
    """
    Media message for WhatsApp (image, video, audio, document).
    """
    
    def __init__(self, 
                 media_type: str,
                 url: Optional[str] = None,
                 file_path: Optional[str] = None,
                 mime_type: Optional[str] = None,
                 file_name: Optional[str] = None,
                 file_size: Optional[int] = None,
                 file_hash: Optional[str] = None,
                 media_key: Optional[str] = None,
                 caption: Optional[str] = None,
                 to: Optional[str] = None,
                 from_jid: Optional[str] = None,
                 id: Optional[str] = None,
                 timestamp: Optional[int] = None,
                 participant: Optional[str] = None,
                 quoted_message_id: Optional[str] = None,
                 quoted_message: Optional[Dict[str, Any]] = None,
                 is_group: bool = False,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 duration: Optional[int] = None,
                 thumbnail: Optional[bytes] = None):
        """
        Initialize a media message.
        
        Args:
            media_type: Type of media (image, video, audio, document)
            url: URL to the media
            file_path: Local path to the media file
            mime_type: MIME type of the media
            file_name: Filename of the media
            file_size: Size of the media in bytes
            file_hash: Hash of the media file
            media_key: Key for decrypting the media
            caption: Caption for the media
            to: Recipient JID or phone number
            from_jid: Sender JID
            id: Message ID
            timestamp: Message timestamp
            participant: Group participant who sent the message
            quoted_message_id: ID of message being quoted/replied to
            quoted_message: Content of the quoted message
            is_group: Whether the message is for a group
            width: Width of the media (for images and videos)
            height: Height of the media (for images and videos)
            duration: Duration of the media in milliseconds (for audio and video)
            thumbnail: Thumbnail data
        """
        super().__init__(
            to=to,
            from_jid=from_jid,
            id=id,
            timestamp=timestamp,
            participant=participant,
            quoted_message_id=quoted_message_id,
            quoted_message=quoted_message,
            is_group=is_group
        )
        self.media_type = media_type
        self.url = url
        self.file_path = file_path
        self.mime_type = mime_type
        self.file_name = file_name
        self.file_size = file_size
        self.file_hash = file_hash
        self.media_key = media_key
        self.caption = caption
        self.width = width
        self.height = height
        self.duration = duration
        self.thumbnail = thumbnail
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the media message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'type': 'media',
            'media_type': self.media_type
        })
        
        if self.url:
            data['url'] = self.url
            
        if self.file_path:
            data['file_path'] = self.file_path
            
        if self.mime_type:
            data['mime_type'] = self.mime_type
            
        if self.file_name:
            data['file_name'] = self.file_name
            
        if self.file_size is not None:
            data['file_size'] = self.file_size
            
        if self.file_hash:
            data['file_hash'] = self.file_hash
            
        if self.media_key:
            data['media_key'] = self.media_key
            
        if self.caption:
            data['caption'] = self.caption
            
        if self.width is not None:
            data['width'] = self.width
            
        if self.height is not None:
            data['height'] = self.height
            
        if self.duration is not None:
            data['duration'] = self.duration
            
        # Don't include thumbnail in the dict to avoid large data
        # Instead, just indicate if it's present
        if self.thumbnail:
            data['has_thumbnail'] = True
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaMessage':
        """
        Create a media message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            MediaMessage instance
        """
        return cls(
            media_type=data.get('media_type', ''),
            url=data.get('url'),
            file_path=data.get('file_path'),
            mime_type=data.get('mime_type'),
            file_name=data.get('file_name'),
            file_size=data.get('file_size'),
            file_hash=data.get('file_hash'),
            media_key=data.get('media_key'),
            caption=data.get('caption'),
            to=data.get('to'),
            from_jid=data.get('from'),
            id=data.get('id'),
            timestamp=data.get('timestamp'),
            participant=data.get('participant'),
            quoted_message_id=data.get('quoted_message_id'),
            quoted_message=data.get('quoted_message'),
            is_group=data.get('is_group', False),
            width=data.get('width'),
            height=data.get('height'),
            duration=data.get('duration'),
            # Thumbnail is not included in dict representations
            thumbnail=None
        )
        
    def __repr__(self) -> str:
        """
        String representation of the media message.
        
        Returns:
            String representation
        """
        return f"<MediaMessage id={self.id} type={self.media_type} name=\"{self.file_name or 'unknown'}\">"

class LocationMessage(Message):
    """
    Location message for WhatsApp.
    """
    
    def __init__(self, 
                 latitude: float,
                 longitude: float,
                 name: Optional[str] = None,
                 address: Optional[str] = None,
                 to: Optional[str] = None,
                 from_jid: Optional[str] = None,
                 id: Optional[str] = None,
                 timestamp: Optional[int] = None,
                 participant: Optional[str] = None,
                 quoted_message_id: Optional[str] = None,
                 quoted_message: Optional[Dict[str, Any]] = None,
                 is_group: bool = False):
        """
        Initialize a location message.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            name: Name of the location
            address: Address of the location
            to: Recipient JID or phone number
            from_jid: Sender JID
            id: Message ID
            timestamp: Message timestamp
            participant: Group participant who sent the message
            quoted_message_id: ID of message being quoted/replied to
            quoted_message: Content of the quoted message
            is_group: Whether the message is for a group
        """
        super().__init__(
            to=to,
            from_jid=from_jid,
            id=id,
            timestamp=timestamp,
            participant=participant,
            quoted_message_id=quoted_message_id,
            quoted_message=quoted_message,
            is_group=is_group
        )
        self.latitude = latitude
        self.longitude = longitude
        self.name = name
        self.address = address
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the location message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'type': 'location',
            'latitude': self.latitude,
            'longitude': self.longitude
        })
        
        if self.name:
            data['name'] = self.name
            
        if self.address:
            data['address'] = self.address
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationMessage':
        """
        Create a location message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            LocationMessage instance
        """
        return cls(
            latitude=data.get('latitude', 0.0),
            longitude=data.get('longitude', 0.0),
            name=data.get('name'),
            address=data.get('address'),
            to=data.get('to'),
            from_jid=data.get('from'),
            id=data.get('id'),
            timestamp=data.get('timestamp'),
            participant=data.get('participant'),
            quoted_message_id=data.get('quoted_message_id'),
            quoted_message=data.get('quoted_message'),
            is_group=data.get('is_group', False)
        )
        
    def __repr__(self) -> str:
        """
        String representation of the location message.
        
        Returns:
            String representation
        """
        return f"<LocationMessage id={self.id} coords=({self.latitude}, {self.longitude})>"

class ContactMessage(Message):
    """
    Contact message for WhatsApp.
    """
    
    def __init__(self, 
                 contacts: List[Dict[str, Any]],
                 to: Optional[str] = None,
                 from_jid: Optional[str] = None,
                 id: Optional[str] = None,
                 timestamp: Optional[int] = None,
                 participant: Optional[str] = None,
                 quoted_message_id: Optional[str] = None,
                 quoted_message: Optional[Dict[str, Any]] = None,
                 is_group: bool = False):
        """
        Initialize a contact message.
        
        Args:
            contacts: List of contact information dictionaries
            to: Recipient JID or phone number
            from_jid: Sender JID
            id: Message ID
            timestamp: Message timestamp
            participant: Group participant who sent the message
            quoted_message_id: ID of message being quoted/replied to
            quoted_message: Content of the quoted message
            is_group: Whether the message is for a group
        """
        super().__init__(
            to=to,
            from_jid=from_jid,
            id=id,
            timestamp=timestamp,
            participant=participant,
            quoted_message_id=quoted_message_id,
            quoted_message=quoted_message,
            is_group=is_group
        )
        self.contacts = contacts
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the contact message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        data = super().to_dict()
        data.update({
            'type': 'contact',
            'contacts': self.contacts
        })
        
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContactMessage':
        """
        Create a contact message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            ContactMessage instance
        """
        return cls(
            contacts=data.get('contacts', []),
            to=data.get('to'),
            from_jid=data.get('from'),
            id=data.get('id'),
            timestamp=data.get('timestamp'),
            participant=data.get('participant'),
            quoted_message_id=data.get('quoted_message_id'),
            quoted_message=data.get('quoted_message'),
            is_group=data.get('is_group', False)
        )
        
    def __repr__(self) -> str:
        """
        String representation of the contact message.
        
        Returns:
            String representation
        """
        contact_count = len(self.contacts)
        return f"<ContactMessage id={self.id} contacts={contact_count}>"

def create_message_from_dict(data: Dict[str, Any]) -> Message:
    """
    Create a message object from a dictionary based on its type.
    
    Args:
        data: Dictionary representation of the message
        
    Returns:
        Appropriate message object
        
    Raises:
        MessageError: If message type is unsupported
    """
    message_type = data.get('type')
    
    if message_type == 'text':
        return TextMessage.from_dict(data)
    elif message_type == 'media':
        return MediaMessage.from_dict(data)
    elif message_type == 'location':
        return LocationMessage.from_dict(data)
    elif message_type == 'contact':
        return ContactMessage.from_dict(data)
    else:
        # Generic message type
        return Message.from_dict(data)
