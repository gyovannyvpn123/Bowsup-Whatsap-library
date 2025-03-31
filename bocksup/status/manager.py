"""
Status management for WhatsApp.

This module handles WhatsApp status updates, including posting and retrieving
status updates, as well as handling status notifications.
"""

import logging
import os
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple, Set, Callable

import aiohttp

from bocksup.common.exceptions import StatusError
from bocksup.common.utils import generate_random_id
from bocksup.common.constants import (
    STATUS_TYPE_AVAILABLE,
    STATUS_TYPE_UNAVAILABLE,
    STATUS_TYPE_TYPING,
    STATUS_TYPE_RECORDING,
    STATUS_TYPE_PAUSED
)

logger = logging.getLogger(__name__)

class Status:
    """
    Represents a WhatsApp status update.
    
    This class encapsulates information about a WhatsApp status update,
    including the content, expiration, and media.
    """
    
    def __init__(self, 
                 id: str,
                 jid: str, 
                 content: Optional[str] = None,
                 media_url: Optional[str] = None,
                 media_type: Optional[str] = None,
                 media_mime: Optional[str] = None,
                 timestamp: Optional[int] = None,
                 expiration: Optional[int] = None,
                 caption: Optional[str] = None):
        """
        Initialize a status update.
        
        Args:
            id: Status ID
            jid: JID of the status owner
            content: Text content of the status (for text statuses)
            media_url: URL to the media (for media statuses)
            media_type: Type of media (image, video, etc.)
            media_mime: MIME type of the media
            timestamp: Timestamp of status creation
            expiration: Timestamp of status expiration
            caption: Caption for media status
        """
        self.id = id
        self.jid = jid
        self.content = content
        self.media_url = media_url
        self.media_type = media_type
        self.media_mime = media_mime
        self.timestamp = timestamp or int(time.time())
        
        # Default expiration is 24 hours from timestamp
        self.expiration = expiration or (self.timestamp + 86400) 
        self.caption = caption
        
        # Derived properties
        self.is_media = bool(media_url)
        self.viewed_by: List[str] = []
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the status to a dictionary.
        
        Returns:
            Dictionary representation of the status
        """
        return {
            'id': self.id,
            'jid': self.jid,
            'content': self.content,
            'media_url': self.media_url,
            'media_type': self.media_type,
            'media_mime': self.media_mime,
            'timestamp': self.timestamp,
            'expiration': self.expiration,
            'caption': self.caption,
            'is_media': self.is_media,
            'viewed_by': self.viewed_by
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Status':
        """
        Create a status from a dictionary.
        
        Args:
            data: Dictionary representation of a status
            
        Returns:
            Status instance
        """
        status = cls(
            id=data.get('id', generate_random_id()),
            jid=data.get('jid', ''),
            content=data.get('content'),
            media_url=data.get('media_url'),
            media_type=data.get('media_type'),
            media_mime=data.get('media_mime'),
            timestamp=data.get('timestamp'),
            expiration=data.get('expiration'),
            caption=data.get('caption')
        )
        
        # Restore additional properties
        if 'viewed_by' in data:
            status.viewed_by = data['viewed_by']
            
        return status
        
    def is_expired(self) -> bool:
        """
        Check if the status is expired.
        
        Returns:
            True if the status is expired
        """
        return int(time.time()) > self.expiration
        
    def __repr__(self) -> str:
        """
        String representation of the status.
        
        Returns:
            String representation
        """
        if self.is_media:
            return f"<Status {self.id} from={self.jid} media_type={self.media_type}>"
        else:
            content_preview = self.content[:20] + "..." if self.content and len(self.content) > 20 else self.content
            return f"<Status {self.id} from={self.jid} content=\"{content_preview}\">"

class PresenceStatus:
    """
    Represents a WhatsApp presence status.
    
    This class tracks the online/offline status, typing state, etc. of a contact.
    """
    
    def __init__(self, 
                 jid: str,
                 status: str = STATUS_TYPE_UNAVAILABLE,
                 last_seen: Optional[int] = None,
                 timestamp: Optional[int] = None):
        """
        Initialize a presence status.
        
        Args:
            jid: JID of the contact
            status: Status type (available, unavailable, typing, etc.)
            last_seen: Timestamp of when the contact was last seen
            timestamp: Timestamp of the status update
        """
        self.jid = jid
        self.status = status
        self.last_seen = last_seen
        self.timestamp = timestamp or int(time.time())
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the presence status to a dictionary.
        
        Returns:
            Dictionary representation of the presence status
        """
        return {
            'jid': self.jid,
            'status': self.status,
            'last_seen': self.last_seen,
            'timestamp': self.timestamp
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PresenceStatus':
        """
        Create a presence status from a dictionary.
        
        Args:
            data: Dictionary representation of a presence status
            
        Returns:
            PresenceStatus instance
        """
        return cls(
            jid=data.get('jid', ''),
            status=data.get('status', STATUS_TYPE_UNAVAILABLE),
            last_seen=data.get('last_seen'),
            timestamp=data.get('timestamp')
        )
        
    def __repr__(self) -> str:
        """
        String representation of the presence status.
        
        Returns:
            String representation
        """
        return f"<PresenceStatus {self.jid} status={self.status}>"

class StatusManager:
    """
    Manages WhatsApp status updates.
    
    This class handles status operations, including posting new statuses,
    retrieving status updates, and handling status notifications.
    """
    
    def __init__(self, 
                 auth_tokens: Dict[str, str],
                 store_path: str = './status',
                 auto_cleanup: bool = True,
                 cleanup_interval: int = 3600,  # 1 hour
                 on_status_update: Optional[Callable[[Status], None]] = None,
                 on_presence_update: Optional[Callable[[PresenceStatus], None]] = None):
        """
        Initialize the status manager.
        
        Args:
            auth_tokens: Authentication tokens for WhatsApp servers
            store_path: Path to store status data
            auto_cleanup: Whether to automatically clean up expired statuses
            cleanup_interval: Interval between auto-cleanups in seconds
            on_status_update: Optional callback for status updates
            on_presence_update: Optional callback for presence updates
        """
        self.auth_tokens = auth_tokens
        self.store_path = store_path
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        self.statuses: Dict[str, Dict[str, Status]] = {}  # JID -> {status_id -> Status}
        self.presence: Dict[str, PresenceStatus] = {}  # JID -> PresenceStatus
        self._cleanup_task = None
        self.on_status_update = on_status_update
        self.on_presence_update = on_presence_update
        
        # Ensure store directory exists
        os.makedirs(store_path, exist_ok=True)
        
    async def start(self) -> None:
        """
        Start the status manager.
        
        This loads statuses from storage and starts auto-cleanup if enabled.
        """
        # Load statuses from storage
        await self.load_statuses()
        await self.load_presence()
        
        # Start auto-cleanup if enabled
        if self.auto_cleanup:
            self._start_auto_cleanup()
            
        logger.info(f"Status manager started")
        
    async def stop(self) -> None:
        """
        Stop the status manager.
        
        This stops auto-cleanup and saves statuses to storage.
        """
        # Stop auto-cleanup if running
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        # Save statuses to storage
        await self.save_statuses()
        await self.save_presence()
        
        logger.info("Status manager stopped")
        
    def _start_auto_cleanup(self) -> None:
        """
        Start automatic status cleanup.
        """
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            
        self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
        
    async def _auto_cleanup_loop(self) -> None:
        """
        Background task that periodically cleans up expired statuses.
        """
        try:
            while True:
                # Clean up expired statuses
                removed = self.cleanup_expired_statuses()
                if removed > 0:
                    logger.debug(f"Auto-cleanup removed {removed} expired statuses")
                    
                # Wait before next cleanup
                await asyncio.sleep(self.cleanup_interval)
                
        except asyncio.CancelledError:
            logger.debug("Auto-cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in auto-cleanup loop: {str(e)}")
            
    def cleanup_expired_statuses(self) -> int:
        """
        Clean up expired statuses.
        
        Returns:
            Number of statuses removed
        """
        removed_count = 0
        current_time = int(time.time())
        
        for jid in list(self.statuses.keys()):
            status_dict = self.statuses[jid]
            expired_ids = [
                status_id for status_id, status in status_dict.items()
                if current_time > status.expiration
            ]
            
            for status_id in expired_ids:
                del status_dict[status_id]
                removed_count += 1
                
            # If no statuses left for this JID, remove the entire entry
            if not status_dict:
                del self.statuses[jid]
                
        return removed_count
        
    async def load_statuses(self) -> int:
        """
        Load statuses from storage.
        
        Returns:
            Number of statuses loaded
            
        Raises:
            StatusError: If loading fails
        """
        try:
            statuses_file = os.path.join(self.store_path, 'statuses.json')
            
            if not os.path.exists(statuses_file):
                logger.info("No statuses file found, starting with empty statuses")
                return 0
                
            with open(statuses_file, 'r') as f:
                statuses_data = json.load(f)
                
            # Clear existing statuses
            self.statuses.clear()
            
            # Load statuses from data
            loaded_count = 0
            for jid, status_dict in statuses_data.items():
                self.statuses[jid] = {}
                for status_id, status_data in status_dict.items():
                    status = Status.from_dict(status_data)
                    # Skip expired statuses
                    if not status.is_expired():
                        self.statuses[jid][status_id] = status
                        loaded_count += 1
                        
                # If no valid statuses for this JID, remove the entry
                if not self.statuses[jid]:
                    del self.statuses[jid]
                    
            logger.info(f"Loaded {loaded_count} statuses from storage")
            
            return loaded_count
            
        except Exception as e:
            logger.error(f"Error loading statuses: {str(e)}")
            raise StatusError(f"Failed to load statuses: {str(e)}")
            
    async def save_statuses(self) -> None:
        """
        Save statuses to storage.
        
        Raises:
            StatusError: If saving fails
        """
        try:
            statuses_file = os.path.join(self.store_path, 'statuses.json')
            
            # Convert statuses to dictionary
            statuses_data = {}
            for jid, status_dict in self.statuses.items():
                statuses_data[jid] = {
                    status_id: status.to_dict()
                    for status_id, status in status_dict.items()
                }
                
            # Write to file
            with open(statuses_file, 'w') as f:
                json.dump(statuses_data, f, indent=2)
                
            logger.info(f"Saved statuses to storage")
            
        except Exception as e:
            logger.error(f"Error saving statuses: {str(e)}")
            raise StatusError(f"Failed to save statuses: {str(e)}")
            
    async def load_presence(self) -> int:
        """
        Load presence data from storage.
        
        Returns:
            Number of presence entries loaded
            
        Raises:
            StatusError: If loading fails
        """
        try:
            presence_file = os.path.join(self.store_path, 'presence.json')
            
            if not os.path.exists(presence_file):
                logger.info("No presence file found, starting with empty presence data")
                return 0
                
            with open(presence_file, 'r') as f:
                presence_data = json.load(f)
                
            # Clear existing presence data
            self.presence.clear()
            
            # Load presence data
            for jid, data in presence_data.items():
                self.presence[jid] = PresenceStatus.from_dict(data)
                
            logger.info(f"Loaded {len(self.presence)} presence entries from storage")
            
            return len(self.presence)
            
        except Exception as e:
            logger.error(f"Error loading presence data: {str(e)}")
            raise StatusError(f"Failed to load presence data: {str(e)}")
            
    async def save_presence(self) -> None:
        """
        Save presence data to storage.
        
        Raises:
            StatusError: If saving fails
        """
        try:
            presence_file = os.path.join(self.store_path, 'presence.json')
            
            # Convert presence data to dictionary
            presence_data = {
                jid: presence.to_dict()
                for jid, presence in self.presence.items()
            }
            
            # Write to file
            with open(presence_file, 'w') as f:
                json.dump(presence_data, f, indent=2)
                
            logger.info(f"Saved presence data to storage")
            
        except Exception as e:
            logger.error(f"Error saving presence data: {str(e)}")
            raise StatusError(f"Failed to save presence data: {str(e)}")
            
    async def post_text_status(self, content: str) -> Status:
        """
        Post a text status update.
        
        Args:
            content: Text content of the status
            
        Returns:
            Created Status instance
            
        Raises:
            StatusError: If posting fails
        """
        logger.info("Posting text status")
        
        try:
            # In a real implementation, this would send a request to WhatsApp servers
            # to post a status update
            
            # Create a status object
            status_id = generate_random_id()
            status = Status(
                id=status_id,
                jid="self",  # In a real implementation, this would be your JID
                content=content,
                timestamp=int(time.time())
            )
            
            # Add status to manager
            if "self" not in self.statuses:
                self.statuses["self"] = {}
                
            self.statuses["self"][status_id] = status
            
            # Save statuses to storage
            await self.save_statuses()
            
            logger.info(f"Posted text status: {status_id}")
            
            return status
            
        except Exception as e:
            logger.error(f"Error posting text status: {str(e)}")
            raise StatusError(f"Failed to post text status: {str(e)}")
            
    async def post_media_status(self, 
                               media_path: str, 
                               media_type: str,
                               caption: Optional[str] = None) -> Status:
        """
        Post a media status update.
        
        Args:
            media_path: Path to the media file
            media_type: Type of media (image, video, etc.)
            caption: Optional caption for the media
            
        Returns:
            Created Status instance
            
        Raises:
            StatusError: If posting fails
        """
        logger.info(f"Posting {media_type} status")
        
        try:
            # Check if media file exists
            if not os.path.exists(media_path):
                raise StatusError(f"Media file not found: {media_path}")
                
            # In a real implementation, this would upload the media file
            # and then send a request to WhatsApp servers to post a status update
            
            # Determine MIME type
            mime_type = None
            if media_type == "image":
                mime_type = "image/jpeg"
            elif media_type == "video":
                mime_type = "video/mp4"
            elif media_type == "audio":
                mime_type = "audio/mp4"
                
            # Create a placeholder media URL
            media_url = f"https://example.com/media/{os.path.basename(media_path)}"
            
            # Create a status object
            status_id = generate_random_id()
            status = Status(
                id=status_id,
                jid="self",  # In a real implementation, this would be your JID
                media_url=media_url,
                media_type=media_type,
                media_mime=mime_type,
                caption=caption,
                timestamp=int(time.time())
            )
            
            # Add status to manager
            if "self" not in self.statuses:
                self.statuses["self"] = {}
                
            self.statuses["self"][status_id] = status
            
            # Save statuses to storage
            await self.save_statuses()
            
            logger.info(f"Posted {media_type} status: {status_id}")
            
            return status
            
        except Exception as e:
            logger.error(f"Error posting media status: {str(e)}")
            raise StatusError(f"Failed to post media status: {str(e)}")
            
    async def delete_status(self, status_id: str) -> bool:
        """
        Delete a status update.
        
        Args:
            status_id: ID of the status to delete
            
        Returns:
            True if successful
            
        Raises:
            StatusError: If deletion fails
        """
        logger.info(f"Deleting status: {status_id}")
        
        try:
            # In a real implementation, this would send a request to WhatsApp servers
            # to delete a status update
            
            # Find the status
            found = False
            for jid, status_dict in self.statuses.items():
                if status_id in status_dict:
                    del status_dict[status_id]
                    found = True
                    break
                    
            if not found:
                raise StatusError(f"Status not found: {status_id}")
                
            # Save statuses to storage
            await self.save_statuses()
            
            logger.info(f"Deleted status: {status_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting status: {str(e)}")
            raise StatusError(f"Failed to delete status: {str(e)}")
            
    def get_contact_statuses(self, jid: str) -> List[Status]:
        """
        Get all statuses posted by a contact.
        
        Args:
            jid: Contact's JID
            
        Returns:
            List of statuses posted by the contact
        """
        if jid not in self.statuses:
            return []
            
        # Get non-expired statuses
        current_time = int(time.time())
        return [
            status for status in self.statuses[jid].values()
            if current_time <= status.expiration
        ]
        
    def get_all_statuses(self) -> List[Status]:
        """
        Get all statuses from all contacts.
        
        Returns:
            List of all statuses
        """
        all_statuses = []
        current_time = int(time.time())
        
        for jid, status_dict in self.statuses.items():
            for status in status_dict.values():
                if current_time <= status.expiration:
                    all_statuses.append(status)
                    
        return all_statuses
        
    def get_status_by_id(self, status_id: str) -> Optional[Status]:
        """
        Get a status by its ID.
        
        Args:
            status_id: Status ID
            
        Returns:
            Status instance or None if not found
        """
        for jid, status_dict in self.statuses.items():
            if status_id in status_dict:
                status = status_dict[status_id]
                if not status.is_expired():
                    return status
                    
        return None
        
    def mark_status_as_viewed(self, status_id: str, viewer_jid: str) -> bool:
        """
        Mark a status as viewed by a contact.
        
        Args:
            status_id: Status ID
            viewer_jid: JID of the viewer
            
        Returns:
            True if successful, False if status not found
        """
        status = self.get_status_by_id(status_id)
        if not status:
            return False
            
        if viewer_jid not in status.viewed_by:
            status.viewed_by.append(viewer_jid)
            return True
            
        return False
        
    def update_presence(self, 
                       jid: str, 
                       status: str, 
                       last_seen: Optional[int] = None) -> PresenceStatus:
        """
        Update a contact's presence status.
        
        Args:
            jid: Contact's JID
            status: Status type (available, unavailable, typing, etc.)
            last_seen: Timestamp of when the contact was last seen
            
        Returns:
            Updated PresenceStatus instance
        """
        now = int(time.time())
        
        # Create or update presence
        if jid in self.presence:
            presence = self.presence[jid]
            presence.status = status
            presence.timestamp = now
            if last_seen is not None:
                presence.last_seen = last_seen
        else:
            presence = PresenceStatus(
                jid=jid,
                status=status,
                last_seen=last_seen,
                timestamp=now
            )
            self.presence[jid] = presence
            
        # Trigger callback if set
        if self.on_presence_update:
            self.on_presence_update(presence)
            
        return presence
        
    def get_presence(self, jid: str) -> Optional[PresenceStatus]:
        """
        Get a contact's presence status.
        
        Args:
            jid: Contact's JID
            
        Returns:
            PresenceStatus instance or None if not found
        """
        return self.presence.get(jid)
        
    def get_available_contacts(self) -> List[str]:
        """
        Get all contacts who are currently available.
        
        Returns:
            List of JIDs of available contacts
        """
        return [
            jid for jid, presence in self.presence.items()
            if presence.status == STATUS_TYPE_AVAILABLE
        ]
        
    def handle_status_notification(self, 
                                  jid: str, 
                                  notification_data: Dict[str, Any]) -> None:
        """
        Handle a status notification.
        
        Args:
            jid: JID of the contact
            notification_data: Notification data
        """
        try:
            # Extract status data
            status_id = notification_data.get('id', generate_random_id())
            content = notification_data.get('content')
            media_url = notification_data.get('media_url')
            media_type = notification_data.get('media_type')
            media_mime = notification_data.get('media_mime')
            caption = notification_data.get('caption')
            timestamp = notification_data.get('timestamp', int(time.time()))
            expiration = notification_data.get('expiration')
            
            # Create status object
            status = Status(
                id=status_id,
                jid=jid,
                content=content,
                media_url=media_url,
                media_type=media_type,
                media_mime=media_mime,
                timestamp=timestamp,
                expiration=expiration,
                caption=caption
            )
            
            # Add status to manager
            if jid not in self.statuses:
                self.statuses[jid] = {}
                
            self.statuses[jid][status_id] = status
            
            # Trigger callback if set
            if self.on_status_update:
                self.on_status_update(status)
                
            logger.info(f"Received status notification from {jid}: {status_id}")
            
        except Exception as e:
            logger.error(f"Error handling status notification: {str(e)}")
