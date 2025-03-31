"""
Utility functions for the Bocksup library.
"""

import random
import string
import time
import uuid
import base64
import hashlib
import re
import logging
from typing import Union, Any, Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def generate_random_id(length: int = 16) -> str:
    """
    Generate a random alphanumeric ID.
    
    Args:
        length: Length of the ID to generate
        
    Returns:
        A random alphanumeric string
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_message_id() -> str:
    """
    Generate a unique message ID in WhatsApp format.
    
    Returns:
        A unique message identifier
    """
    # Format: 3EB0XXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    suffix = str(uuid.uuid4()).upper()
    prefix = "3EB0"
    return f"{prefix}{suffix[4:]}"

def timestamp_now() -> int:
    """
    Get current timestamp in milliseconds.
    
    Returns:
        Current timestamp in milliseconds
    """
    return int(time.time() * 1000)

def format_phone_number(phone: str) -> str:
    """
    Format a phone number to WhatsApp's expected format.
    
    Args:
        phone: Phone number to format
        
    Returns:
        Formatted phone number (country code + number)
    """
    # Remove any non-digit characters
    clean_number = re.sub(r'\D', '', phone)
    
    # Ensure it has a country code
    if not clean_number.startswith('+'):
        if len(clean_number) == 10:  # US number without country code
            clean_number = f"1{clean_number}"
        clean_number = f"+{clean_number}"
        
    return clean_number

def is_valid_phone_number(phone: str) -> bool:
    """
    Check if a phone number is valid.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if the phone number is valid
    """
    # Basic validation - could be enhanced
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))

def phone_to_jid(phone: str) -> str:
    """
    Convert a phone number to a JID (Jabber ID) used by WhatsApp.
    
    Args:
        phone: Phone number to convert
        
    Returns:
        JID for the phone number
    """
    # Clean the phone number
    clean_phone = re.sub(r'\D', '', phone)
    return f"{clean_phone}@s.whatsapp.net"

def to_bytes(data: Union[str, bytes]) -> bytes:
    """
    Convert various data types to bytes.
    
    Args:
        data: Data to convert
        
    Returns:
        Data converted to bytes
    """
    if isinstance(data, bytes):
        return data
    elif isinstance(data, str):
        return data.encode('utf-8')
    else:
        return str(data).encode('utf-8')

def from_bytes(data: bytes) -> str:
    """
    Convert bytes to string.
    
    Args:
        data: Bytes to convert
        
    Returns:
        Decoded string
    """
    return data.decode('utf-8', errors='replace')

def base64_encode(data: Union[str, bytes]) -> str:
    """
    Base64 encode data.
    
    Args:
        data: Data to encode
        
    Returns:
        Base64 encoded string
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')

def base64_decode(data: str) -> bytes:
    """
    Base64 decode data.
    
    Args:
        data: Base64 encoded string
        
    Returns:
        Decoded bytes
    """
    return base64.b64decode(data)

def sha256(data: Union[str, bytes]) -> bytes:
    """
    Calculate SHA-256 hash.
    
    Args:
        data: Data to hash
        
    Returns:
        SHA-256 hash as bytes
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).digest()

def hmac_sha256(key: Union[str, bytes], data: Union[str, bytes]) -> bytes:
    """
    Calculate HMAC-SHA256.
    
    Args:
        key: Key for HMAC
        data: Data to hash
        
    Returns:
        HMAC-SHA256 hash as bytes
    """
    import hmac
    
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(data, str):
        data = data.encode('utf-8')
        
    return hmac.new(key, data, hashlib.sha256).digest()

def chunked_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def safe_str(obj: Any) -> str:
    """
    Safely convert any object to string, handling exceptions.
    
    Args:
        obj: Object to convert
        
    Returns:
        String representation of the object
    """
    try:
        return str(obj)
    except Exception as e:
        logger.warning(f"Failed to convert object to string: {e}")
        return "[Object conversion error]"

def parse_jid(jid: str) -> Tuple[str, Optional[str]]:
    """
    Parse a JID into its components.
    
    Args:
        jid: JID to parse (e.g., "123456789@s.whatsapp.net" or "123456789-123456789@g.us")
        
    Returns:
        Tuple of (user, domain) or (group_id, domain)
    """
    parts = jid.split('@')
    if len(parts) != 2:
        raise ValueError(f"Invalid JID format: {jid}")
    
    user = parts[0]
    domain = parts[1]
    
    return (user, domain)

def is_group_jid(jid: str) -> bool:
    """
    Check if a JID represents a group.
    
    Args:
        jid: JID to check
        
    Returns:
        True if the JID is for a group
    """
    return jid.endswith("@g.us")
