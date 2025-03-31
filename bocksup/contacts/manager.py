"""
Contact management for WhatsApp.

This module handles WhatsApp contacts, including synchronization, storage,
querying, and contact-related operations.
"""

import logging
import os
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple, Set

from bocksup.common.exceptions import ContactError
from bocksup.common.utils import phone_to_jid

logger = logging.getLogger(__name__)

class Contact:
    """
    Represents a WhatsApp contact.
    
    This class encapsulates information about a WhatsApp contact,
    including their JID, name, phone number, and other attributes.
    """
    
    def __init__(self, 
                 jid: str, 
                 name: Optional[str] = None,
                 phone: Optional[str] = None,
                 status: Optional[str] = None,
                 picture_id: Optional[str] = None,
                 is_business: bool = False,
                 last_seen: Optional[int] = None,
                 short_name: Optional[str] = None,
                 group_membership: Optional[List[str]] = None):
        """
        Initialize a contact.
        
        Args:
            jid: Contact's JID (e.g., 1234567890@s.whatsapp.net)
            name: Contact's name
            phone: Contact's phone number
            status: Contact's status message
            picture_id: ID of contact's profile picture
            is_business: Whether the contact is a business account
            last_seen: Timestamp of when the contact was last seen
            short_name: Short name or nickname
            group_membership: List of group JIDs the contact belongs to
        """
        self.jid = jid
        self.name = name
        
        # Extract phone number from JID if not provided
        if not phone and '@' in jid:
            self.phone = jid.split('@')[0]
        else:
            self.phone = phone
            
        self.status = status
        self.picture_id = picture_id
        self.is_business = is_business
        self.last_seen = last_seen
        self.short_name = short_name
        self.group_membership = group_membership or []
        
        # Additional metadata
        self.last_updated = int(time.time())
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the contact to a dictionary.
        
        Returns:
            Dictionary representation of the contact
        """
        return {
            'jid': self.jid,
            'name': self.name,
            'phone': self.phone,
            'status': self.status,
            'picture_id': self.picture_id,
            'is_business': self.is_business,
            'last_seen': self.last_seen,
            'short_name': self.short_name,
            'group_membership': self.group_membership,
            'last_updated': self.last_updated
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contact':
        """
        Create a contact from a dictionary.
        
        Args:
            data: Dictionary representation of a contact
            
        Returns:
            Contact instance
        """
        contact = cls(
            jid=data.get('jid', ''),
            name=data.get('name'),
            phone=data.get('phone'),
            status=data.get('status'),
            picture_id=data.get('picture_id'),
            is_business=data.get('is_business', False),
            last_seen=data.get('last_seen'),
            short_name=data.get('short_name'),
            group_membership=data.get('group_membership', [])
        )
        
        # Restore metadata
        if 'last_updated' in data:
            contact.last_updated = data['last_updated']
            
        return contact
        
    def __repr__(self) -> str:
        """
        String representation of the contact.
        
        Returns:
            String representation
        """
        return f"<Contact {self.jid} name='{self.name}'>"
        
    def __eq__(self, other: object) -> bool:
        """
        Compare two contacts.
        
        Args:
            other: Object to compare with
            
        Returns:
            True if contacts are equal (based on JID)
        """
        if not isinstance(other, Contact):
            return False
            
        return self.jid == other.jid
        
    def __hash__(self) -> int:
        """
        Hash of the contact.
        
        Returns:
            Hash value based on JID
        """
        return hash(self.jid)

class ContactManager:
    """
    Manages WhatsApp contacts.
    
    This class handles contact synchronization, storage, querying,
    and contact-related operations.
    """
    
    def __init__(self, 
                 auth_tokens: Dict[str, str],
                 store_path: str = './contacts',
                 auto_sync: bool = True,
                 sync_interval: int = 3600):  # 1 hour
        """
        Initialize the contact manager.
        
        Args:
            auth_tokens: Authentication tokens for WhatsApp servers
            store_path: Path to store contact data
            auto_sync: Whether to automatically sync contacts
            sync_interval: Interval between auto-syncs in seconds
        """
        self.auth_tokens = auth_tokens
        self.store_path = store_path
        self.auto_sync = auto_sync
        self.sync_interval = sync_interval
        self.contacts: Dict[str, Contact] = {}
        self.last_sync = 0
        self._sync_task = None
        
        # Ensure store directory exists
        os.makedirs(store_path, exist_ok=True)
        
    async def start(self) -> None:
        """
        Start the contact manager.
        
        This loads contacts from storage and starts auto-sync if enabled.
        """
        # Load contacts from storage
        await self.load_contacts()
        
        # Start auto-sync if enabled
        if self.auto_sync:
            self._start_auto_sync()
            
        logger.info(f"Contact manager started with {len(self.contacts)} contacts")
        
    async def stop(self) -> None:
        """
        Stop the contact manager.
        
        This stops auto-sync and saves contacts to storage.
        """
        # Stop auto-sync if running
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
                
        # Save contacts to storage
        await self.save_contacts()
        
        logger.info("Contact manager stopped")
        
    def _start_auto_sync(self) -> None:
        """
        Start automatic contact synchronization.
        """
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            
        self._sync_task = asyncio.create_task(self._auto_sync_loop())
        
    async def _auto_sync_loop(self) -> None:
        """
        Background task that periodically syncs contacts.
        """
        try:
            while True:
                # Check if it's time to sync
                time_since_sync = time.time() - self.last_sync
                
                if time_since_sync >= self.sync_interval:
                    logger.debug("Auto-syncing contacts")
                    try:
                        await self.sync_contacts()
                    except Exception as e:
                        logger.error(f"Error during auto-sync: {str(e)}")
                        
                # Wait before next check
                await asyncio.sleep(min(60, self.sync_interval / 10))
                
        except asyncio.CancelledError:
            logger.debug("Auto-sync task cancelled")
        except Exception as e:
            logger.error(f"Error in auto-sync loop: {str(e)}")
            
    async def sync_contacts(self) -> int:
        """
        Synchronize contacts with WhatsApp servers.
        
        Returns:
            Number of contacts updated or added
            
        Raises:
            ContactError: If sync fails
        """
        logger.info("Synchronizing contacts with server")
        
        try:
            # This is a placeholder for the actual sync implementation
            # In a real implementation, this would connect to WhatsApp servers
            # and retrieve the contact list
            
            # For this example, we'll assume no new contacts
            # In a real implementation, this would process server data
            
            # Update last sync time
            self.last_sync = time.time()
            
            # Save contacts to storage
            await self.save_contacts()
            
            logger.info(f"Contact sync completed, {len(self.contacts)} contacts")
            
            return 0  # No contacts updated in this placeholder implementation
            
        except Exception as e:
            logger.error(f"Error syncing contacts: {str(e)}")
            raise ContactError(f"Contact sync failed: {str(e)}")
            
    async def load_contacts(self) -> int:
        """
        Load contacts from storage.
        
        Returns:
            Number of contacts loaded
            
        Raises:
            ContactError: If loading fails
        """
        try:
            contacts_file = os.path.join(self.store_path, 'contacts.json')
            
            if not os.path.exists(contacts_file):
                logger.info("No contacts file found, starting with empty contacts")
                return 0
                
            with open(contacts_file, 'r') as f:
                contacts_data = json.load(f)
                
            # Clear existing contacts
            self.contacts.clear()
            
            # Load contacts from data
            for jid, contact_data in contacts_data.items():
                self.contacts[jid] = Contact.from_dict(contact_data)
                
            logger.info(f"Loaded {len(self.contacts)} contacts from storage")
            
            return len(self.contacts)
            
        except Exception as e:
            logger.error(f"Error loading contacts: {str(e)}")
            raise ContactError(f"Failed to load contacts: {str(e)}")
            
    async def save_contacts(self) -> None:
        """
        Save contacts to storage.
        
        Raises:
            ContactError: If saving fails
        """
        try:
            contacts_file = os.path.join(self.store_path, 'contacts.json')
            
            # Convert contacts to dictionary
            contacts_data = {jid: contact.to_dict() for jid, contact in self.contacts.items()}
            
            # Write to file
            with open(contacts_file, 'w') as f:
                json.dump(contacts_data, f, indent=2)
                
            logger.info(f"Saved {len(self.contacts)} contacts to storage")
            
        except Exception as e:
            logger.error(f"Error saving contacts: {str(e)}")
            raise ContactError(f"Failed to save contacts: {str(e)}")
            
    def get_contact(self, identifier: str) -> Optional[Contact]:
        """
        Get a contact by JID or phone number.
        
        Args:
            identifier: JID or phone number
            
        Returns:
            Contact instance or None if not found
        """
        # Check if it's a JID
        if '@' in identifier:
            return self.contacts.get(identifier)
            
        # If it's a phone number, convert to JID first
        jid = phone_to_jid(identifier)
        return self.contacts.get(jid)
        
    def get_all_contacts(self) -> List[Contact]:
        """
        Get all contacts.
        
        Returns:
            List of all contacts
        """
        return list(self.contacts.values())
        
    def add_contact(self, contact: Contact) -> None:
        """
        Add or update a contact.
        
        Args:
            contact: Contact to add or update
        """
        self.contacts[contact.jid] = contact
        logger.debug(f"Added/updated contact: {contact.jid}")
        
    def remove_contact(self, jid: str) -> bool:
        """
        Remove a contact.
        
        Args:
            jid: JID of the contact to remove
            
        Returns:
            True if contact was removed, False if not found
        """
        if jid in self.contacts:
            del self.contacts[jid]
            logger.debug(f"Removed contact: {jid}")
            return True
            
        logger.debug(f"Contact not found for removal: {jid}")
        return False
        
    def search_contacts(self, query: str) -> List[Contact]:
        """
        Search contacts by name or phone number.
        
        Args:
            query: Search query
            
        Returns:
            List of matching contacts
        """
        query = query.lower()
        results = []
        
        for contact in self.contacts.values():
            # Check name match
            if contact.name and query in contact.name.lower():
                results.append(contact)
                continue
                
            # Check phone match
            if contact.phone and query in contact.phone:
                results.append(contact)
                continue
                
        return results
        
    def update_contact_status(self, jid: str, status: str) -> bool:
        """
        Update a contact's status message.
        
        Args:
            jid: Contact's JID
            status: New status message
            
        Returns:
            True if contact was updated, False if not found
        """
        contact = self.get_contact(jid)
        if not contact:
            return False
            
        contact.status = status
        contact.last_updated = int(time.time())
        return True
        
    def update_contact_picture(self, jid: str, picture_id: str) -> bool:
        """
        Update a contact's profile picture ID.
        
        Args:
            jid: Contact's JID
            picture_id: New profile picture ID
            
        Returns:
            True if contact was updated, False if not found
        """
        contact = self.get_contact(jid)
        if not contact:
            return False
            
        contact.picture_id = picture_id
        contact.last_updated = int(time.time())
        return True
        
    def update_contact_last_seen(self, jid: str, timestamp: int) -> bool:
        """
        Update a contact's last seen timestamp.
        
        Args:
            jid: Contact's JID
            timestamp: Last seen timestamp
            
        Returns:
            True if contact was updated, False if not found
        """
        contact = self.get_contact(jid)
        if not contact:
            return False
            
        contact.last_seen = timestamp
        contact.last_updated = int(time.time())
        return True
        
    def update_group_membership(self, jid: str, group_jid: str, is_member: bool) -> bool:
        """
        Update a contact's group membership.
        
        Args:
            jid: Contact's JID
            group_jid: Group's JID
            is_member: Whether the contact is a member of the group
            
        Returns:
            True if contact was updated, False if not found
        """
        contact = self.get_contact(jid)
        if not contact:
            return False
            
        if is_member and group_jid not in contact.group_membership:
            contact.group_membership.append(group_jid)
        elif not is_member and group_jid in contact.group_membership:
            contact.group_membership.remove(group_jid)
            
        contact.last_updated = int(time.time())
        return True
        
    def get_contacts_in_group(self, group_jid: str) -> List[Contact]:
        """
        Get all contacts who are members of a specific group.
        
        Args:
            group_jid: Group's JID
            
        Returns:
            List of contacts in the group
        """
        return [
            contact for contact in self.contacts.values()
            if group_jid in contact.group_membership
        ]
        
    def get_recently_active_contacts(self, hours: int = 24) -> List[Contact]:
        """
        Get contacts who were recently active.
        
        Args:
            hours: Time window in hours
            
        Returns:
            List of recently active contacts
        """
        now = int(time.time())
        cutoff = now - (hours * 3600)
        
        return [
            contact for contact in self.contacts.values()
            if contact.last_seen and contact.last_seen > cutoff
        ]
