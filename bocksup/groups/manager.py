"""
Group management for WhatsApp.

This module handles WhatsApp groups, including creation, management,
modification, and group-specific operations.
"""

import logging
import os
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple, Set, Callable

import aiohttp

from bocksup.common.exceptions import GroupError
from bocksup.common.constants import GROUP_CREATE, GROUP_SUBJECT, GROUP_ADD, GROUP_REMOVE, GROUP_LEAVE, GROUP_PHOTO
from bocksup.common.utils import generate_random_id

logger = logging.getLogger(__name__)

class Group:
    """
    Represents a WhatsApp group.
    
    This class encapsulates information about a WhatsApp group,
    including its JID, name, participants, and other attributes.
    """
    
    def __init__(self, 
                 jid: str, 
                 subject: Optional[str] = None,
                 creator: Optional[str] = None,
                 creation_time: Optional[int] = None,
                 participants: Optional[Dict[str, str]] = None,
                 admins: Optional[List[str]] = None,
                 description: Optional[str] = None,
                 picture_id: Optional[str] = None):
        """
        Initialize a group.
        
        Args:
            jid: Group's JID (e.g., 1234567890-1234567890@g.us)
            subject: Group subject (name)
            creator: JID of the group creator
            creation_time: Timestamp of group creation
            participants: Dictionary of participant JIDs to participant types
            admins: List of admin JIDs
            description: Group description
            picture_id: ID of group picture
        """
        self.jid = jid
        self.subject = subject or ""
        self.creator = creator
        self.creation_time = creation_time or int(time.time())
        self.participants = participants or {}
        self.admins = admins or []
        self.description = description or ""
        self.picture_id = picture_id
        
        # Additional metadata
        self.last_updated = int(time.time())
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the group to a dictionary.
        
        Returns:
            Dictionary representation of the group
        """
        return {
            'jid': self.jid,
            'subject': self.subject,
            'creator': self.creator,
            'creation_time': self.creation_time,
            'participants': self.participants,
            'admins': self.admins,
            'description': self.description,
            'picture_id': self.picture_id,
            'last_updated': self.last_updated
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Group':
        """
        Create a group from a dictionary.
        
        Args:
            data: Dictionary representation of a group
            
        Returns:
            Group instance
        """
        group = cls(
            jid=data.get('jid', ''),
            subject=data.get('subject'),
            creator=data.get('creator'),
            creation_time=data.get('creation_time'),
            participants=data.get('participants', {}),
            admins=data.get('admins', []),
            description=data.get('description'),
            picture_id=data.get('picture_id')
        )
        
        # Restore metadata
        if 'last_updated' in data:
            group.last_updated = data['last_updated']
            
        return group
        
    def __repr__(self) -> str:
        """
        String representation of the group.
        
        Returns:
            String representation
        """
        return f"<Group {self.jid} subject='{self.subject}'>"
        
    def __eq__(self, other: object) -> bool:
        """
        Compare two groups.
        
        Args:
            other: Object to compare with
            
        Returns:
            True if groups are equal (based on JID)
        """
        if not isinstance(other, Group):
            return False
            
        return self.jid == other.jid
        
    def __hash__(self) -> int:
        """
        Hash of the group.
        
        Returns:
            Hash value based on JID
        """
        return hash(self.jid)
        
    def is_admin(self, jid: str) -> bool:
        """
        Check if a user is an admin of the group.
        
        Args:
            jid: User's JID
            
        Returns:
            True if the user is an admin
        """
        return jid in self.admins
        
    def is_participant(self, jid: str) -> bool:
        """
        Check if a user is a participant of the group.
        
        Args:
            jid: User's JID
            
        Returns:
            True if the user is a participant
        """
        return jid in self.participants
        
    def get_participant_count(self) -> int:
        """
        Get the number of participants in the group.
        
        Returns:
            Number of participants
        """
        return len(self.participants)

class GroupManager:
    """
    Manages WhatsApp groups.
    
    This class handles group operations, including creation, modification,
    participant management, and group-related operations.
    """
    
    def __init__(self, 
                 auth_tokens: Dict[str, str],
                 store_path: str = './groups',
                 auto_sync: bool = True,
                 sync_interval: int = 3600,  # 1 hour
                 on_group_event: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """
        Initialize the group manager.
        
        Args:
            auth_tokens: Authentication tokens for WhatsApp servers
            store_path: Path to store group data
            auto_sync: Whether to automatically sync groups
            sync_interval: Interval between auto-syncs in seconds
            on_group_event: Optional callback for group events
        """
        self.auth_tokens = auth_tokens
        self.store_path = store_path
        self.auto_sync = auto_sync
        self.sync_interval = sync_interval
        self.groups: Dict[str, Group] = {}
        self.last_sync = 0
        self._sync_task = None
        self.on_group_event = on_group_event
        
        # Ensure store directory exists
        os.makedirs(store_path, exist_ok=True)
        
    async def start(self) -> None:
        """
        Start the group manager.
        
        This loads groups from storage and starts auto-sync if enabled.
        """
        # Load groups from storage
        await self.load_groups()
        
        # Start auto-sync if enabled
        if self.auto_sync:
            self._start_auto_sync()
            
        logger.info(f"Group manager started with {len(self.groups)} groups")
        
    async def stop(self) -> None:
        """
        Stop the group manager.
        
        This stops auto-sync and saves groups to storage.
        """
        # Stop auto-sync if running
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
                
        # Save groups to storage
        await self.save_groups()
        
        logger.info("Group manager stopped")
        
    def _start_auto_sync(self) -> None:
        """
        Start automatic group synchronization.
        """
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            
        self._sync_task = asyncio.create_task(self._auto_sync_loop())
        
    async def _auto_sync_loop(self) -> None:
        """
        Background task that periodically syncs groups.
        """
        try:
            while True:
                # Check if it's time to sync
                time_since_sync = time.time() - self.last_sync
                
                if time_since_sync >= self.sync_interval:
                    logger.debug("Auto-syncing groups")
                    try:
                        await self.sync_groups()
                    except Exception as e:
                        logger.error(f"Error during auto-sync: {str(e)}")
                        
                # Wait before next check
                await asyncio.sleep(min(60, self.sync_interval / 10))
                
        except asyncio.CancelledError:
            logger.debug("Auto-sync task cancelled")
        except Exception as e:
            logger.error(f"Error in auto-sync loop: {str(e)}")
            
    async def sync_groups(self) -> int:
        """
        Synchronize groups with WhatsApp servers.
        
        Returns:
            Number of groups updated or added
            
        Raises:
            GroupError: If sync fails
        """
        logger.info("Synchronizing groups with server")
        
        try:
            # In a real implementation, this would connect to WhatsApp servers
            # and retrieve the group list
            
            # For this example, we'll assume no new groups
            # In a real implementation, this would process server data
            
            # Update last sync time
            self.last_sync = time.time()
            
            # Save groups to storage
            await self.save_groups()
            
            logger.info(f"Group sync completed, {len(self.groups)} groups")
            
            return 0  # No groups updated in this placeholder implementation
            
        except Exception as e:
            logger.error(f"Error syncing groups: {str(e)}")
            raise GroupError(f"Group sync failed: {str(e)}")
            
    async def load_groups(self) -> int:
        """
        Load groups from storage.
        
        Returns:
            Number of groups loaded
            
        Raises:
            GroupError: If loading fails
        """
        try:
            groups_file = os.path.join(self.store_path, 'groups.json')
            
            if not os.path.exists(groups_file):
                logger.info("No groups file found, starting with empty groups")
                return 0
                
            with open(groups_file, 'r') as f:
                groups_data = json.load(f)
                
            # Clear existing groups
            self.groups.clear()
            
            # Load groups from data
            for jid, group_data in groups_data.items():
                self.groups[jid] = Group.from_dict(group_data)
                
            logger.info(f"Loaded {len(self.groups)} groups from storage")
            
            return len(self.groups)
            
        except Exception as e:
            logger.error(f"Error loading groups: {str(e)}")
            raise GroupError(f"Failed to load groups: {str(e)}")
            
    async def save_groups(self) -> None:
        """
        Save groups to storage.
        
        Raises:
            GroupError: If saving fails
        """
        try:
            groups_file = os.path.join(self.store_path, 'groups.json')
            
            # Convert groups to dictionary
            groups_data = {jid: group.to_dict() for jid, group in self.groups.items()}
            
            # Write to file
            with open(groups_file, 'w') as f:
                json.dump(groups_data, f, indent=2)
                
            logger.info(f"Saved {len(self.groups)} groups to storage")
            
        except Exception as e:
            logger.error(f"Error saving groups: {str(e)}")
            raise GroupError(f"Failed to save groups: {str(e)}")
            
    def get_group(self, jid: str) -> Optional[Group]:
        """
        Get a group by JID.
        
        Args:
            jid: Group's JID
            
        Returns:
            Group instance or None if not found
        """
        return self.groups.get(jid)
        
    def get_all_groups(self) -> List[Group]:
        """
        Get all groups.
        
        Returns:
            List of all groups
        """
        return list(self.groups.values())
        
    async def create_group(self, 
                          subject: str, 
                          participants: List[str]) -> Group:
        """
        Create a new WhatsApp group.
        
        Args:
            subject: Group subject (name)
            participants: List of participant JIDs to add to the group
            
        Returns:
            Newly created Group instance
            
        Raises:
            GroupError: If group creation fails
        """
        logger.info(f"Creating group: {subject} with {len(participants)} participants")
        
        try:
            # In a real implementation, this would send a request to WhatsApp servers
            # to create a new group
            
            # For this example, we'll create a placeholder group locally
            group_id = generate_random_id(15)
            jid = f"{group_id}@g.us"
            
            # Create group object
            group = Group(
                jid=jid,
                subject=subject,
                creator="self",  # In a real implementation, this would be your JID
                creation_time=int(time.time()),
                participants={p: "regular" for p in participants},
                admins=["self"]  # In a real implementation, this would be your JID
            )
            
            # Add group to manager
            self.groups[jid] = group
            
            # Save groups to storage
            await self.save_groups()
            
            # Trigger event callback if set
            if self.on_group_event:
                self.on_group_event(GROUP_CREATE, {
                    'group': group.to_dict(),
                    'action': GROUP_CREATE,
                    'subject': subject,
                    'participants': participants
                })
                
            logger.info(f"Group created: {jid}")
            
            return group
            
        except Exception as e:
            logger.error(f"Error creating group: {str(e)}")
            raise GroupError(f"Group creation failed: {str(e)}")
            
    async def leave_group(self, jid: str) -> bool:
        """
        Leave a WhatsApp group.
        
        Args:
            jid: Group's JID
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If leaving fails
        """
        logger.info(f"Leaving group: {jid}")
        
        try:
            # Check if group exists
            group = self.get_group(jid)
            if not group:
                raise GroupError(f"Group not found: {jid}")
                
            # In a real implementation, this would send a request to WhatsApp servers
            # to leave the group
            
            # Remove group from manager
            del self.groups[jid]
            
            # Save groups to storage
            await self.save_groups()
            
            # Trigger event callback if set
            if self.on_group_event:
                self.on_group_event(GROUP_LEAVE, {
                    'group_jid': jid,
                    'action': GROUP_LEAVE
                })
                
            logger.info(f"Left group: {jid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error leaving group: {str(e)}")
            raise GroupError(f"Failed to leave group: {str(e)}")
            
    async def add_participants(self, 
                              jid: str, 
                              participants: List[str]) -> bool:
        """
        Add participants to a WhatsApp group.
        
        Args:
            jid: Group's JID
            participants: List of participant JIDs to add
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If adding participants fails
        """
        logger.info(f"Adding {len(participants)} participants to group: {jid}")
        
        try:
            # Check if group exists
            group = self.get_group(jid)
            if not group:
                raise GroupError(f"Group not found: {jid}")
                
            # In a real implementation, this would send a request to WhatsApp servers
            # to add participants to the group
            
            # Add participants to group object
            for participant in participants:
                if participant not in group.participants:
                    group.participants[participant] = "regular"
                    
            # Update last updated timestamp
            group.last_updated = int(time.time())
            
            # Save groups to storage
            await self.save_groups()
            
            # Trigger event callback if set
            if self.on_group_event:
                self.on_group_event(GROUP_ADD, {
                    'group_jid': jid,
                    'action': GROUP_ADD,
                    'participants': participants
                })
                
            logger.info(f"Added participants to group: {jid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding participants: {str(e)}")
            raise GroupError(f"Failed to add participants: {str(e)}")
            
    async def remove_participants(self, 
                                jid: str, 
                                participants: List[str]) -> bool:
        """
        Remove participants from a WhatsApp group.
        
        Args:
            jid: Group's JID
            participants: List of participant JIDs to remove
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If removing participants fails
        """
        logger.info(f"Removing {len(participants)} participants from group: {jid}")
        
        try:
            # Check if group exists
            group = self.get_group(jid)
            if not group:
                raise GroupError(f"Group not found: {jid}")
                
            # In a real implementation, this would send a request to WhatsApp servers
            # to remove participants from the group
            
            # Remove participants from group object
            for participant in participants:
                if participant in group.participants:
                    del group.participants[participant]
                    
                # Also remove from admins if present
                if participant in group.admins:
                    group.admins.remove(participant)
                    
            # Update last updated timestamp
            group.last_updated = int(time.time())
            
            # Save groups to storage
            await self.save_groups()
            
            # Trigger event callback if set
            if self.on_group_event:
                self.on_group_event(GROUP_REMOVE, {
                    'group_jid': jid,
                    'action': GROUP_REMOVE,
                    'participants': participants
                })
                
            logger.info(f"Removed participants from group: {jid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing participants: {str(e)}")
            raise GroupError(f"Failed to remove participants: {str(e)}")
            
    async def promote_to_admin(self, jid: str, participants: List[str]) -> bool:
        """
        Promote participants to admin status in a WhatsApp group.
        
        Args:
            jid: Group's JID
            participants: List of participant JIDs to promote
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If promotion fails
        """
        logger.info(f"Promoting {len(participants)} participants to admin in group: {jid}")
        
        try:
            # Check if group exists
            group = self.get_group(jid)
            if not group:
                raise GroupError(f"Group not found: {jid}")
                
            # In a real implementation, this would send a request to WhatsApp servers
            # to promote participants to admin
            
            # Promote participants in group object
            for participant in participants:
                if participant in group.participants and participant not in group.admins:
                    group.admins.append(participant)
                    group.participants[participant] = "admin"
                    
            # Update last updated timestamp
            group.last_updated = int(time.time())
            
            # Save groups to storage
            await self.save_groups()
            
            logger.info(f"Promoted participants to admin in group: {jid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error promoting participants: {str(e)}")
            raise GroupError(f"Failed to promote participants: {str(e)}")
            
    async def demote_from_admin(self, jid: str, participants: List[str]) -> bool:
        """
        Demote participants from admin status in a WhatsApp group.
        
        Args:
            jid: Group's JID
            participants: List of participant JIDs to demote
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If demotion fails
        """
        logger.info(f"Demoting {len(participants)} participants from admin in group: {jid}")
        
        try:
            # Check if group exists
            group = self.get_group(jid)
            if not group:
                raise GroupError(f"Group not found: {jid}")
                
            # In a real implementation, this would send a request to WhatsApp servers
            # to demote participants from admin
            
            # Demote participants in group object
            for participant in participants:
                if participant in group.admins:
                    group.admins.remove(participant)
                    if participant in group.participants:
                        group.participants[participant] = "regular"
                        
            # Update last updated timestamp
            group.last_updated = int(time.time())
            
            # Save groups to storage
            await self.save_groups()
            
            logger.info(f"Demoted participants from admin in group: {jid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error demoting participants: {str(e)}")
            raise GroupError(f"Failed to demote participants: {str(e)}")
            
    async def set_subject(self, jid: str, subject: str) -> bool:
        """
        Set the subject (name) of a WhatsApp group.
        
        Args:
            jid: Group's JID
            subject: New group subject
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If setting subject fails
        """
        logger.info(f"Setting subject of group {jid} to: {subject}")
        
        try:
            # Check if group exists
            group = self.get_group(jid)
            if not group:
                raise GroupError(f"Group not found: {jid}")
                
            # In a real implementation, this would send a request to WhatsApp servers
            # to set the group subject
            
            # Update group object
            group.subject = subject
            group.last_updated = int(time.time())
            
            # Save groups to storage
            await self.save_groups()
            
            # Trigger event callback if set
            if self.on_group_event:
                self.on_group_event(GROUP_SUBJECT, {
                    'group_jid': jid,
                    'action': GROUP_SUBJECT,
                    'subject': subject
                })
                
            logger.info(f"Set subject of group {jid} to: {subject}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting group subject: {str(e)}")
            raise GroupError(f"Failed to set group subject: {str(e)}")
            
    async def set_description(self, jid: str, description: str) -> bool:
        """
        Set the description of a WhatsApp group.
        
        Args:
            jid: Group's JID
            description: New group description
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If setting description fails
        """
        logger.info(f"Setting description of group {jid}")
        
        try:
            # Check if group exists
            group = self.get_group(jid)
            if not group:
                raise GroupError(f"Group not found: {jid}")
                
            # In a real implementation, this would send a request to WhatsApp servers
            # to set the group description
            
            # Update group object
            group.description = description
            group.last_updated = int(time.time())
            
            # Save groups to storage
            await self.save_groups()
            
            logger.info(f"Set description of group {jid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting group description: {str(e)}")
            raise GroupError(f"Failed to set group description: {str(e)}")
            
    async def set_picture(self, jid: str, image_path: str) -> bool:
        """
        Set the picture of a WhatsApp group.
        
        Args:
            jid: Group's JID
            image_path: Path to the image file
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If setting picture fails
        """
        logger.info(f"Setting picture of group {jid}")
        
        try:
            # Check if group exists
            group = self.get_group(jid)
            if not group:
                raise GroupError(f"Group not found: {jid}")
                
            # Check if image file exists
            if not os.path.exists(image_path):
                raise GroupError(f"Image file not found: {image_path}")
                
            # In a real implementation, this would send a request to WhatsApp servers
            # to set the group picture
            
            # Update group object with a placeholder picture ID
            group.picture_id = generate_random_id(10)
            group.last_updated = int(time.time())
            
            # Save groups to storage
            await self.save_groups()
            
            # Trigger event callback if set
            if self.on_group_event:
                self.on_group_event(GROUP_PHOTO, {
                    'group_jid': jid,
                    'action': GROUP_PHOTO,
                    'picture_id': group.picture_id
                })
                
            logger.info(f"Set picture of group {jid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting group picture: {str(e)}")
            raise GroupError(f"Failed to set group picture: {str(e)}")
            
    def get_participant_groups(self, jid: str) -> List[Group]:
        """
        Get all groups a participant is a member of.
        
        Args:
            jid: Participant's JID
            
        Returns:
            List of groups the participant is a member of
        """
        return [
            group for group in self.groups.values()
            if jid in group.participants
        ]
        
    def get_admin_groups(self, jid: str) -> List[Group]:
        """
        Get all groups a participant is an admin of.
        
        Args:
            jid: Participant's JID
            
        Returns:
            List of groups the participant is an admin of
        """
        return [
            group for group in self.groups.values()
            if jid in group.admins
        ]
        
    def update_group_from_notification(self, 
                                     group_jid: str, 
                                     notification_type: str, 
                                     notification_data: Dict[str, Any]) -> bool:
        """
        Update a group based on a notification.
        
        Args:
            group_jid: Group's JID
            notification_type: Type of notification (add, remove, subject, etc.)
            notification_data: Notification data
            
        Returns:
            True if group was updated, False otherwise
        """
        logger.debug(f"Updating group {group_jid} from notification: {notification_type}")
        
        # Get group
        group = self.get_group(group_jid)
        
        # If group doesn't exist, create it
        if not group:
            group = Group(
                jid=group_jid,
                subject=notification_data.get('subject', ''),
                creator=notification_data.get('creator')
            )
            self.groups[group_jid] = group
            
        # Update group based on notification type
        if notification_type == GROUP_SUBJECT:
            # Subject change
            group.subject = notification_data.get('subject', group.subject)
            
        elif notification_type == GROUP_ADD:
            # Participants added
            participants = notification_data.get('participants', [])
            for participant in participants:
                group.participants[participant] = "regular"
                
        elif notification_type == GROUP_REMOVE:
            # Participants removed
            participants = notification_data.get('participants', [])
            for participant in participants:
                if participant in group.participants:
                    del group.participants[participant]
                if participant in group.admins:
                    group.admins.remove(participant)
                    
        elif notification_type == GROUP_PHOTO:
            # Picture updated
            group.picture_id = notification_data.get('picture_id')
            
        # Update last updated timestamp
        group.last_updated = int(time.time())
        
        # Save groups asynchronously
        asyncio.create_task(self.save_groups())
        
        return True
