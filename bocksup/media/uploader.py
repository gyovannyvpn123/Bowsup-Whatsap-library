"""
Media uploader for WhatsApp.

This module handles the uploading of media files to WhatsApp servers,
including chunking large files, handling retries, and progress reporting.
"""

import logging
import os
import mimetypes
import asyncio
import time
import hashlib
from typing import Dict, Any, Optional, Callable, Union, BinaryIO, Tuple

import aiohttp

from bocksup.common.exceptions import MediaError
from bocksup.common.constants import WHATSAPP_MEDIA_SERVER

logger = logging.getLogger(__name__)

class MediaUploader:
    """
    Handles uploading media files to WhatsApp servers.
    
    This class manages the process of uploading media files of various types,
    handling chunking for large files, retries for failed uploads,
    and progress reporting.
    """
    
    def __init__(self, 
                 auth_tokens: Dict[str, str],
                 max_chunk_size: int = 512 * 1024,  # 512KB default chunk size
                 retry_count: int = 3,
                 timeout: int = 30):
        """
        Initialize the media uploader.
        
        Args:
            auth_tokens: Authentication tokens for WhatsApp servers
            max_chunk_size: Maximum size of upload chunks in bytes
            retry_count: Number of retry attempts for failed uploads
            timeout: Upload timeout in seconds
        """
        self.auth_tokens = auth_tokens
        self.max_chunk_size = max_chunk_size
        self.retry_count = retry_count
        self.timeout = timeout
        self.upload_url = f"https://{WHATSAPP_MEDIA_SERVER}/v1/media/upload"
        
    async def upload(self, 
                     file_path: str, 
                     media_type: str, 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
        """
        Upload a media file to WhatsApp servers.
        
        Args:
            file_path: Path to the media file
            media_type: Type of media (image, video, audio, document)
            progress_callback: Optional callback for upload progress
            
        Returns:
            Dictionary with upload details including URL and media info
            
        Raises:
            MediaError: If upload fails
        """
        logger.info(f"Uploading media file: {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise MediaError(f"File not found: {file_path}")
                
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            mime_type = self._get_mime_type(file_path)
            
            logger.debug(f"File info: {file_name}, {file_size} bytes, {mime_type}")
            
            # Calculate hash for file
            file_hash = await self._calculate_file_hash(file_path)
            
            # Initialize upload
            upload_info = await self._initialize_upload(
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                media_type=media_type,
                file_hash=file_hash
            )
            
            # Get upload token and session ID
            upload_token = upload_info.get('upload_token')
            session_id = upload_info.get('session_id')
            
            if not upload_token or not session_id:
                raise MediaError("Failed to initialize upload: Missing upload token or session ID")
                
            # Upload file content
            await self._upload_file_chunks(
                file_path=file_path,
                file_size=file_size,
                session_id=session_id,
                upload_token=upload_token,
                progress_callback=progress_callback
            )
            
            # Finalize upload
            media_info = await self._finalize_upload(
                session_id=session_id,
                upload_token=upload_token,
                file_hash=file_hash
            )
            
            logger.info(f"Media upload successful: {file_name}")
            
            return {
                'url': media_info.get('url'),
                'mime_type': mime_type,
                'file_name': file_name,
                'file_size': file_size,
                'media_key': media_info.get('media_key'),
                'file_hash': file_hash,
                'media_type': media_type
            }
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Media upload failed: {str(e)}")
            raise MediaError(f"Media upload failed: {str(e)}")
            
    async def upload_from_bytes(self, 
                               file_data: bytes, 
                               file_name: str,
                               media_type: str,
                               mime_type: Optional[str] = None,
                               progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
        """
        Upload media from bytes data.
        
        Args:
            file_data: Bytes containing the file data
            file_name: Name for the file
            media_type: Type of media (image, video, audio, document)
            mime_type: MIME type of the media (if None, guessed from file_name)
            progress_callback: Optional callback for upload progress
            
        Returns:
            Dictionary with upload details including URL and media info
            
        Raises:
            MediaError: If upload fails
        """
        logger.info(f"Uploading media from bytes data, filename: {file_name}")
        
        try:
            # Get file info
            file_size = len(file_data)
            
            if mime_type is None:
                mime_type = self._get_mime_type(file_name)
                
            logger.debug(f"File info: {file_name}, {file_size} bytes, {mime_type}")
            
            # Calculate hash for data
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Initialize upload
            upload_info = await self._initialize_upload(
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                media_type=media_type,
                file_hash=file_hash
            )
            
            # Get upload token and session ID
            upload_token = upload_info.get('upload_token')
            session_id = upload_info.get('session_id')
            
            if not upload_token or not session_id:
                raise MediaError("Failed to initialize upload: Missing upload token or session ID")
                
            # Upload file content in chunks
            await self._upload_bytes_chunks(
                file_data=file_data,
                file_size=file_size,
                session_id=session_id,
                upload_token=upload_token,
                progress_callback=progress_callback
            )
            
            # Finalize upload
            media_info = await self._finalize_upload(
                session_id=session_id,
                upload_token=upload_token,
                file_hash=file_hash
            )
            
            logger.info(f"Media upload successful: {file_name}")
            
            return {
                'url': media_info.get('url'),
                'mime_type': mime_type,
                'file_name': file_name,
                'file_size': file_size,
                'media_key': media_info.get('media_key'),
                'file_hash': file_hash,
                'media_type': media_type
            }
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Media upload failed: {str(e)}")
            raise MediaError(f"Media upload failed: {str(e)}")
            
    async def _initialize_upload(self, 
                                file_name: str, 
                                file_size: int, 
                                mime_type: str,
                                media_type: str,
                                file_hash: str) -> Dict[str, Any]:
        """
        Initialize an upload session with WhatsApp media servers.
        
        Args:
            file_name: Name of the file
            file_size: Size of the file in bytes
            mime_type: MIME type of the file
            media_type: Type of media (image, video, audio, document)
            file_hash: SHA-256 hash of the file
            
        Returns:
            Dictionary with upload session details
            
        Raises:
            MediaError: If initialization fails
        """
        logger.debug("Initializing media upload")
        
        try:
            # Prepare request data
            headers = {
                'Authorization': f"Bearer {self.auth_tokens.get('server_token', '')}",
                'Content-Type': 'application/json'
            }
            
            data = {
                'file_name': file_name,
                'file_size': file_size,
                'mime_type': mime_type,
                'media_type': media_type,
                'file_hash': file_hash
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.upload_url}/init",
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise MediaError(
                            f"Upload initialization failed with status {response.status}: {error_text}"
                        )
                        
                    result = await response.json()
                    
                    if not result.get('success', False):
                        raise MediaError(
                            f"Upload initialization failed: {result.get('error', 'Unknown error')}"
                        )
                        
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during upload initialization: {str(e)}")
            raise MediaError(f"Network error during upload initialization: {str(e)}")
            
    async def _upload_file_chunks(self,
                                 file_path: str,
                                 file_size: int,
                                 session_id: str,
                                 upload_token: str,
                                 progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """
        Upload a file in chunks.
        
        Args:
            file_path: Path to the file
            file_size: Size of the file in bytes
            session_id: Upload session ID
            upload_token: Upload token
            progress_callback: Optional callback for upload progress
            
        Raises:
            MediaError: If chunk upload fails
        """
        logger.debug(f"Uploading file in chunks: {file_path}")
        
        uploaded_bytes = 0
        chunk_number = 0
        
        # Prepare headers for chunk upload
        headers = {
            'Authorization': f"Bearer {self.auth_tokens.get('server_token', '')}",
            'X-Session-ID': session_id,
            'X-Upload-Token': upload_token
        }
        
        try:
            with open(file_path, 'rb') as f:
                while uploaded_bytes < file_size:
                    # Calculate chunk size
                    chunk_size = min(self.max_chunk_size, file_size - uploaded_bytes)
                    
                    # Read chunk
                    chunk_data = f.read(chunk_size)
                    
                    # Upload chunk with retries
                    for attempt in range(self.retry_count + 1):
                        try:
                            await self._upload_chunk(
                                chunk_data=chunk_data,
                                chunk_number=chunk_number,
                                offset=uploaded_bytes,
                                headers=headers
                            )
                            break  # Successful upload, break retry loop
                        except MediaError as e:
                            if attempt < self.retry_count:
                                logger.warning(
                                    f"Chunk upload failed (attempt {attempt+1}/{self.retry_count+1}): {str(e)}. Retrying..."
                                )
                                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                            else:
                                # Last attempt failed
                                raise
                                
                    # Update progress
                    uploaded_bytes += chunk_size
                    chunk_number += 1
                    
                    if progress_callback:
                        progress_callback(uploaded_bytes, file_size)
                        
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Error reading or uploading file: {str(e)}")
            raise MediaError(f"Error reading or uploading file: {str(e)}")
            
    async def _upload_bytes_chunks(self,
                                  file_data: bytes,
                                  file_size: int,
                                  session_id: str,
                                  upload_token: str,
                                  progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """
        Upload bytes data in chunks.
        
        Args:
            file_data: Bytes containing the file data
            file_size: Size of the data in bytes
            session_id: Upload session ID
            upload_token: Upload token
            progress_callback: Optional callback for upload progress
            
        Raises:
            MediaError: If chunk upload fails
        """
        logger.debug("Uploading bytes data in chunks")
        
        uploaded_bytes = 0
        chunk_number = 0
        
        # Prepare headers for chunk upload
        headers = {
            'Authorization': f"Bearer {self.auth_tokens.get('server_token', '')}",
            'X-Session-ID': session_id,
            'X-Upload-Token': upload_token
        }
        
        try:
            while uploaded_bytes < file_size:
                # Calculate chunk size
                chunk_size = min(self.max_chunk_size, file_size - uploaded_bytes)
                
                # Get chunk
                chunk_data = file_data[uploaded_bytes:uploaded_bytes+chunk_size]
                
                # Upload chunk with retries
                for attempt in range(self.retry_count + 1):
                    try:
                        await self._upload_chunk(
                            chunk_data=chunk_data,
                            chunk_number=chunk_number,
                            offset=uploaded_bytes,
                            headers=headers
                        )
                        break  # Successful upload, break retry loop
                    except MediaError as e:
                        if attempt < self.retry_count:
                            logger.warning(
                                f"Chunk upload failed (attempt {attempt+1}/{self.retry_count+1}): {str(e)}. Retrying..."
                            )
                            await asyncio.sleep(1 * (attempt +.1))  # Exponential backoff
                        else:
                            # Last attempt failed
                            raise
                            
                # Update progress
                uploaded_bytes += chunk_size
                chunk_number += 1
                
                if progress_callback:
                    progress_callback(uploaded_bytes, file_size)
                    
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Error uploading chunks: {str(e)}")
            raise MediaError(f"Error uploading chunks: {str(e)}")
            
    async def _upload_chunk(self,
                           chunk_data: bytes,
                           chunk_number: int,
                           offset: int,
                           headers: Dict[str, str]) -> None:
        """
        Upload a single chunk to the server.
        
        Args:
            chunk_data: Chunk data to upload
            chunk_number: Number of the chunk
            offset: Offset in the file
            headers: HTTP headers for the request
            
        Raises:
            MediaError: If chunk upload fails
        """
        try:
            # Additional headers for this chunk
            chunk_headers = headers.copy()
            chunk_headers.update({
                'Content-Type': 'application/octet-stream',
                'X-Chunk-Number': str(chunk_number),
                'X-Chunk-Offset': str(offset)
            })
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.upload_url}/chunk",
                    data=chunk_data,
                    headers=chunk_headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise MediaError(
                            f"Chunk upload failed with status {response.status}: {error_text}"
                        )
                        
                    result = await response.json()
                    
                    if not result.get('success', False):
                        raise MediaError(
                            f"Chunk upload failed: {result.get('error', 'Unknown error')}"
                        )
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error during chunk upload: {str(e)}")
            raise MediaError(f"Network error during chunk upload: {str(e)}")
            
    async def _finalize_upload(self,
                              session_id: str,
                              upload_token: str,
                              file_hash: str) -> Dict[str, Any]:
        """
        Finalize an upload session.
        
        Args:
            session_id: Upload session ID
            upload_token: Upload token
            file_hash: SHA-256 hash of the file
            
        Returns:
            Dictionary with media information
            
        Raises:
            MediaError: If finalization fails
        """
        logger.debug("Finalizing media upload")
        
        try:
            # Prepare request data
            headers = {
                'Authorization': f"Bearer {self.auth_tokens.get('server_token', '')}",
                'Content-Type': 'application/json',
                'X-Session-ID': session_id,
                'X-Upload-Token': upload_token
            }
            
            data = {
                'file_hash': file_hash
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.upload_url}/finalize",
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise MediaError(
                            f"Upload finalization failed with status {response.status}: {error_text}"
                        )
                        
                    result = await response.json()
                    
                    if not result.get('success', False):
                        raise MediaError(
                            f"Upload finalization failed: {result.get('error', 'Unknown error')}"
                        )
                        
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during upload finalization: {str(e)}")
            raise MediaError(f"Network error during upload finalization: {str(e)}")
            
    async def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash as a hexadecimal string
            
        Raises:
            MediaError: If hash calculation fails
        """
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                # Read file in chunks to avoid loading large files into memory
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
                    
                    # Allow other tasks to run occasionally
                    if hasattr(asyncio, "create_task"):
                        await asyncio.sleep(0)
                        
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating file hash: {str(e)}")
            raise MediaError(f"Error calculating file hash: {str(e)}")
            
    def _get_mime_type(self, file_path: str) -> str:
        """
        Get MIME type of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if not mime_type:
            # Default to application/octet-stream for unknown types
            extension = os.path.splitext(file_path)[1].lower()
            
            # Try to determine MIME type from common extensions
            if extension in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif extension == '.png':
                mime_type = 'image/png'
            elif extension == '.gif':
                mime_type = 'image/gif'
            elif extension in ['.mp4', '.mpeg4']:
                mime_type = 'video/mp4'
            elif extension == '.webp':
                mime_type = 'image/webp'
            elif extension in ['.mp3', '.mpeg3']:
                mime_type = 'audio/mpeg'
            elif extension == '.ogg':
                mime_type = 'audio/ogg'
            elif extension == '.pdf':
                mime_type = 'application/pdf'
            else:
                mime_type = 'application/octet-stream'
                
        return mime_type
