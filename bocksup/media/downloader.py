"""
Media downloader for WhatsApp.

This module handles the downloading of media files from WhatsApp servers,
including handling retries, validation, and progress reporting.
"""

import logging
import os
import asyncio
import hashlib
import time
from typing import Dict, Any, Optional, Callable, BinaryIO, Union

import aiohttp

from bocksup.common.exceptions import MediaError
from bocksup.common.constants import WHATSAPP_MEDIA_SERVER

logger = logging.getLogger(__name__)

class MediaDownloader:
    """
    Handles downloading media files from WhatsApp servers.
    
    This class manages the process of downloading media files of various types,
    handling retries for failed downloads, validation of downloaded content,
    and progress reporting.
    """
    
    def __init__(self, 
                 auth_tokens: Dict[str, str],
                 download_path: str = './media',
                 chunk_size: int = 1024 * 1024,  # 1MB default chunk size
                 retry_count: int = 3,
                 timeout: int = 30):
        """
        Initialize the media downloader.
        
        Args:
            auth_tokens: Authentication tokens for WhatsApp servers
            download_path: Path to store downloaded media
            chunk_size: Size of download chunks in bytes
            retry_count: Number of retry attempts for failed downloads
            timeout: Download timeout in seconds
        """
        self.auth_tokens = auth_tokens
        self.download_path = download_path
        self.chunk_size = chunk_size
        self.retry_count = retry_count
        self.timeout = timeout
        
        # Ensure download directory exists
        os.makedirs(download_path, exist_ok=True)
        
    async def download(self, 
                      url: str, 
                      file_name: Optional[str] = None,
                      media_key: Optional[str] = None,
                      file_hash: Optional[str] = None,
                      auto_filename: bool = True,
                      progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """
        Download a media file from WhatsApp servers.
        
        Args:
            url: URL of the media
            file_name: Optional name for the downloaded file
            media_key: Optional media key for decryption
            file_hash: Optional hash for verification
            auto_filename: Generate filename from URL if not provided
            progress_callback: Optional callback for download progress
            
        Returns:
            Path to the downloaded file
            
        Raises:
            MediaError: If download fails
        """
        logger.info(f"Downloading media from: {url}")
        
        try:
            # Ensure we have a file name
            if not file_name and auto_filename:
                file_name = self._extract_filename_from_url(url)
                
            if not file_name:
                raise MediaError("No file name provided and couldn't extract from URL")
                
            # Prepare the full file path
            file_path = os.path.join(self.download_path, file_name)
            
            # Check if file already exists with matching hash
            if file_hash and os.path.exists(file_path):
                existing_hash = await self._calculate_file_hash(file_path)
                if existing_hash == file_hash:
                    logger.info(f"File already exists with matching hash: {file_path}")
                    return file_path
                    
            # Prepare headers for download
            headers = {
                'Authorization': f"Bearer {self.auth_tokens.get('server_token', '')}",
                'User-Agent': 'Bocksup/0.1.0'
            }
            
            # Add media key if provided
            if media_key:
                headers['X-Media-Key'] = media_key
                
            # Download file with retries
            for attempt in range(self.retry_count + 1):
                try:
                    await self._download_file(
                        url=url,
                        file_path=file_path,
                        headers=headers,
                        progress_callback=progress_callback
                    )
                    
                    break  # Successful download, break retry loop
                except MediaError as e:
                    if attempt < self.retry_count:
                        logger.warning(
                            f"Download failed (attempt {attempt+1}/{self.retry_count+1}): {str(e)}. Retrying..."
                        )
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    else:
                        # Last attempt failed
                        raise
                        
            # Verify file hash if provided
            if file_hash:
                downloaded_hash = await self._calculate_file_hash(file_path)
                if downloaded_hash != file_hash:
                    os.remove(file_path)
                    raise MediaError(
                        f"Hash verification failed. Expected: {file_hash}, got: {downloaded_hash}"
                    )
                    
            logger.info(f"Media download successful: {file_path}")
            return file_path
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Media download failed: {str(e)}")
            
            # Clean up partial download if file exists
            if file_name and os.path.exists(os.path.join(self.download_path, file_name)):
                try:
                    os.remove(os.path.join(self.download_path, file_name))
                except:
                    pass
                    
            raise MediaError(f"Media download failed: {str(e)}")
            
    async def download_to_bytes(self, 
                               url: str,
                               media_key: Optional[str] = None,
                               file_hash: Optional[str] = None,
                               progress_callback: Optional[Callable[[int, int], None]] = None) -> bytes:
        """
        Download a media file to bytes.
        
        Args:
            url: URL of the media
            media_key: Optional media key for decryption
            file_hash: Optional hash for verification
            progress_callback: Optional callback for download progress
            
        Returns:
            Bytes containing the file data
            
        Raises:
            MediaError: If download fails
        """
        logger.info(f"Downloading media to bytes from: {url}")
        
        try:
            # Prepare headers for download
            headers = {
                'Authorization': f"Bearer {self.auth_tokens.get('server_token', '')}",
                'User-Agent': 'Bocksup/0.1.0'
            }
            
            # Add media key if provided
            if media_key:
                headers['X-Media-Key'] = media_key
                
            # Download file with retries
            for attempt in range(self.retry_count + 1):
                try:
                    data = await self._download_to_bytes(
                        url=url,
                        headers=headers,
                        progress_callback=progress_callback
                    )
                    
                    break  # Successful download, break retry loop
                except MediaError as e:
                    if attempt < self.retry_count:
                        logger.warning(
                            f"Download failed (attempt {attempt+1}/{self.retry_count+1}): {str(e)}. Retrying..."
                        )
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    else:
                        # Last attempt failed
                        raise
                        
            # Verify file hash if provided
            if file_hash:
                downloaded_hash = hashlib.sha256(data).hexdigest()
                if downloaded_hash != file_hash:
                    raise MediaError(
                        f"Hash verification failed. Expected: {file_hash}, got: {downloaded_hash}"
                    )
                    
            logger.info(f"Media download to bytes successful ({len(data)} bytes)")
            return data
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Media download to bytes failed: {str(e)}")
            raise MediaError(f"Media download to bytes failed: {str(e)}")
            
    async def _download_file(self, 
                            url: str, 
                            file_path: str, 
                            headers: Dict[str, str],
                            progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """
        Download a file from a URL to a local path.
        
        Args:
            url: URL to download from
            file_path: Path to save the file
            headers: HTTP headers for the request
            progress_callback: Optional callback for download progress
            
        Raises:
            MediaError: If download fails
        """
        try:
            # Ensure download path exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create temp file path
            temp_file_path = f"{file_path}.temp"
            
            # Initialize progress variables
            downloaded_bytes = 0
            total_bytes = 0
            
            # Open file for writing
            with open(temp_file_path, 'wb') as f:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        headers=headers,
                        timeout=self.timeout,
                        raise_for_status=True
                    ) as response:
                        # Get content length if available
                        if 'Content-Length' in response.headers:
                            total_bytes = int(response.headers['Content-Length'])
                            
                        # Download file in chunks
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded_bytes += len(chunk)
                                
                                # Update progress
                                if progress_callback and total_bytes > 0:
                                    progress_callback(downloaded_bytes, total_bytes)
                                    
            # Rename temp file to final file
            os.rename(temp_file_path, file_path)
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error during download: {str(e)}")
            
            # Clean up temp file if it exists
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                    
            raise MediaError(f"Network error during download: {str(e)}")
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            
            # Clean up temp file if it exists
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                    
            raise MediaError(f"Error downloading file: {str(e)}")
            
    async def _download_to_bytes(self, 
                                url: str, 
                                headers: Dict[str, str],
                                progress_callback: Optional[Callable[[int, int], None]] = None) -> bytes:
        """
        Download a file from a URL to bytes.
        
        Args:
            url: URL to download from
            headers: HTTP headers for the request
            progress_callback: Optional callback for download progress
            
        Returns:
            Bytes containing the file data
            
        Raises:
            MediaError: If download fails
        """
        try:
            # Initialize progress variables
            downloaded_bytes = 0
            total_bytes = 0
            chunks = []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    raise_for_status=True
                ) as response:
                    # Get content length if available
                    if 'Content-Length' in response.headers:
                        total_bytes = int(response.headers['Content-Length'])
                        
                    # Download file in chunks
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        if chunk:
                            chunks.append(chunk)
                            downloaded_bytes += len(chunk)
                            
                            # Update progress
                            if progress_callback and total_bytes > 0:
                                progress_callback(downloaded_bytes, total_bytes)
                                
            # Combine chunks into a single bytes object
            return b''.join(chunks)
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error during download: {str(e)}")
            raise MediaError(f"Network error during download: {str(e)}")
        except Exception as e:
            logger.error(f"Error downloading to bytes: {str(e)}")
            raise MediaError(f"Error downloading to bytes: {str(e)}")
            
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
            
    def _extract_filename_from_url(self, url: str) -> str:
        """
        Extract filename from a URL.
        
        Args:
            url: URL to extract filename from
            
        Returns:
            Extracted filename or a generated one
        """
        # Try to extract filename from URL
        try:
            from urllib.parse import urlparse
            path = urlparse(url).path
            filename = os.path.basename(path)
            
            # If filename has no extension or is empty, generate one
            if not filename or '.' not in filename:
                # Generate a filename based on timestamp
                timestamp = int(time.time())
                filename = f"media_{timestamp}"
                
            return filename
            
        except Exception:
            # In case of any error, generate a filename
            timestamp = int(time.time())
            return f"media_{timestamp}"
