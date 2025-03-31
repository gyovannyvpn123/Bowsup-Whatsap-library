"""
Media processor for WhatsApp media handling.

This module provides functionality for processing media files before
sending or after receiving, including image resizing, format conversion,
thumbnail generation, and metadata extraction.
"""

import logging
import os
import io
import tempfile
import asyncio
import mimetypes
import hashlib
from typing import Dict, Any, Optional, Tuple, Union, BinaryIO, List

from PIL import Image, ExifTags
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from bocksup.common.exceptions import MediaError
from bocksup.common.constants import (
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_VIDEO,
    MEDIA_TYPE_AUDIO,
    MEDIA_TYPE_DOCUMENT,
    MEDIA_TYPE_STICKER
)

logger = logging.getLogger(__name__)

class MediaProcessor:
    """
    Handles processing of media files for WhatsApp.
    
    This class provides methods for preparing media before sending,
    including image resizing, format conversion, and thumbnail generation.
    It also handles processing received media.
    """
    
    def __init__(self, 
                 max_image_dimension: int = 1600,
                 image_quality: int = 70,
                 thumbnail_dimension: int = 100,
                 max_gif_size: int = 10 * 1024 * 1024,  # 10MB
                 temp_dir: Optional[str] = None):
        """
        Initialize the media processor.
        
        Args:
            max_image_dimension: Maximum dimension (width or height) for images
            image_quality: JPEG compression quality (0-100)
            thumbnail_dimension: Size of generated thumbnails
            max_gif_size: Maximum size for GIF files before conversion
            temp_dir: Directory for temporary files
        """
        self.max_image_dimension = max_image_dimension
        self.image_quality = image_quality
        self.thumbnail_dimension = thumbnail_dimension
        self.max_gif_size = max_gif_size
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
    async def process_outgoing_image(self, 
                                    file_path: str, 
                                    preserve_exif: bool = True) -> Dict[str, Any]:
        """
        Process an image before sending.
        
        Args:
            file_path: Path to the image file
            preserve_exif: Whether to preserve EXIF data
            
        Returns:
            Dictionary with processed image details
            
        Raises:
            MediaError: If processing fails
        """
        logger.info(f"Processing outgoing image: {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise MediaError(f"File not found: {file_path}")
                
            # Open the image
            img = Image.open(file_path)
            
            # Get original format and EXIF data
            original_format = img.format
            exif_data = None
            
            if preserve_exif and hasattr(img, '_getexif') and img._getexif():
                exif_data = img._getexif()
                
            # Check if resizing is needed
            width, height = img.size
            original_dimensions = (width, height)
            
            if width > self.max_image_dimension or height > self.max_image_dimension:
                # Calculate new dimensions
                if width > height:
                    new_width = self.max_image_dimension
                    new_height = int(height * (self.max_image_dimension / width))
                else:
                    new_height = self.max_image_dimension
                    new_width = int(width * (self.max_image_dimension / height))
                    
                # Resize image
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
            # Convert format if needed
            output_format = original_format
            if original_format not in ['JPEG', 'PNG', 'WEBP']:
                output_format = 'JPEG'
                
            # Create a BytesIO object for the output
            output_buffer = io.BytesIO()
            
            # Save the image
            if output_format == 'JPEG':
                # For JPEG, we can set quality
                if exif_data and preserve_exif:
                    # Convert EXIF to bytes
                    exif_bytes = self._exif_dict_to_bytes(exif_data)
                    img.save(output_buffer, format='JPEG', quality=self.image_quality, exif=exif_bytes)
                else:
                    img.save(output_buffer, format='JPEG', quality=self.image_quality)
            else:
                # For other formats
                img.save(output_buffer, format=output_format)
                
            # Generate thumbnail
            thumbnail_buffer = await self._generate_thumbnail(img)
            
            # Get the processed image data
            processed_data = output_buffer.getvalue()
            thumbnail_data = thumbnail_buffer.getvalue()
            
            # Calculate the hash of the processed image
            img_hash = hashlib.sha256(processed_data).hexdigest()
            
            # Get MIME type
            mime_type = self._get_mime_type_from_format(output_format)
            
            # Get filename extension
            extension = self._get_extension_from_format(output_format)
            
            # Create output filename
            filename = os.path.splitext(os.path.basename(file_path))[0]
            output_filename = f"{filename}.{extension}"
            
            logger.info(f"Image processed successfully: {original_dimensions} -> {img.size}, format: {output_format}")
            
            return {
                'data': processed_data,
                'thumbnail': thumbnail_data,
                'width': img.size[0],
                'height': img.size[1],
                'original_width': original_dimensions[0],
                'original_height': original_dimensions[1],
                'mime_type': mime_type,
                'file_name': output_filename,
                'file_size': len(processed_data),
                'file_hash': img_hash,
                'media_type': MEDIA_TYPE_IMAGE
            }
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise MediaError(f"Image processing failed: {str(e)}")
            
    async def process_outgoing_video(self, 
                                    file_path: str, 
                                    generate_preview: bool = True) -> Dict[str, Any]:
        """
        Process a video before sending.
        
        Args:
            file_path: Path to the video file
            generate_preview: Whether to generate a video preview/thumbnail
            
        Returns:
            Dictionary with processed video details
            
        Raises:
            MediaError: If processing fails
        """
        logger.info(f"Processing outgoing video: {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise MediaError(f"File not found: {file_path}")
                
            # For video processing, we might need additional libraries
            # Here we'll just extract basic info and generate a thumbnail if requested
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            mime_type = self._get_mime_type(file_path)
            
            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)
            
            # Initialize video dimensions (if we can't determine them, use None)
            width = None
            height = None
            duration = None
            
            # Generate preview/thumbnail if requested
            thumbnail_data = None
            if generate_preview:
                try:
                    # Try to extract first frame for thumbnail
                    # This requires installing opencv-python
                    thumbnail_data = await self._extract_video_thumbnail(file_path)
                except Exception as e:
                    logger.warning(f"Failed to generate video thumbnail: {str(e)}")
                    
            logger.info(f"Video processed successfully: {file_path}, size: {file_size} bytes")
            
            result = {
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'mime_type': mime_type,
                'file_hash': file_hash,
                'media_type': MEDIA_TYPE_VIDEO
            }
            
            if width is not None and height is not None:
                result['width'] = width
                result['height'] = height
                
            if duration is not None:
                result['duration'] = duration
                
            if thumbnail_data:
                result['thumbnail'] = thumbnail_data
                
            return result
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise MediaError(f"Video processing failed: {str(e)}")
            
    async def process_outgoing_audio(self, file_path: str) -> Dict[str, Any]:
        """
        Process an audio file before sending.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary with processed audio details
            
        Raises:
            MediaError: If processing fails
        """
        logger.info(f"Processing outgoing audio: {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise MediaError(f"File not found: {file_path}")
                
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            mime_type = self._get_mime_type(file_path)
            
            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)
            
            # Initialize audio duration (if we can't determine it, use None)
            duration = None
            
            # Try to get audio duration using mutagen if available
            try:
                import mutagen
                audio = mutagen.File(file_path)
                if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                    duration = int(audio.info.length * 1000)  # Convert to milliseconds
            except ImportError:
                logger.debug("mutagen library not available for audio duration extraction")
            except Exception as e:
                logger.debug(f"Failed to extract audio duration: {str(e)}")
                
            logger.info(f"Audio processed successfully: {file_path}, size: {file_size} bytes")
            
            result = {
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'mime_type': mime_type,
                'file_hash': file_hash,
                'media_type': MEDIA_TYPE_AUDIO
            }
            
            if duration is not None:
                result['duration'] = duration
                
            return result
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise MediaError(f"Audio processing failed: {str(e)}")
            
    async def process_outgoing_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document before sending.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with processed document details
            
        Raises:
            MediaError: If processing fails
        """
        logger.info(f"Processing outgoing document: {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise MediaError(f"File not found: {file_path}")
                
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            mime_type = self._get_mime_type(file_path)
            
            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)
            
            logger.info(f"Document processed successfully: {file_path}, size: {file_size} bytes")
            
            return {
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'mime_type': mime_type,
                'file_hash': file_hash,
                'media_type': MEDIA_TYPE_DOCUMENT
            }
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise MediaError(f"Document processing failed: {str(e)}")
            
    async def process_outgoing_sticker(self, file_path: str) -> Dict[str, Any]:
        """
        Process a sticker image before sending.
        
        Args:
            file_path: Path to the sticker image file
            
        Returns:
            Dictionary with processed sticker details
            
        Raises:
            MediaError: If processing fails
        """
        logger.info(f"Processing outgoing sticker: {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise MediaError(f"File not found: {file_path}")
                
            # Open the image
            img = Image.open(file_path)
            
            # Check format - WebP is preferred for stickers
            output_format = 'WEBP'
            
            # Resize if needed (WhatsApp has specific size requirements for stickers)
            width, height = img.size
            original_dimensions = (width, height)
            
            # Ensure the image has transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            # Resize to appropriate dimensions if needed
            # WhatsApp stickers are typically 512x512
            if width != 512 or height != 512:
                img = img.resize((512, 512), Image.LANCZOS)
                
            # Create a BytesIO object for the output
            output_buffer = io.BytesIO()
            
            # Save the image as WebP
            img.save(output_buffer, format='WEBP', lossless=True)
            
            # Generate thumbnail
            thumbnail_buffer = await self._generate_thumbnail(img)
            
            # Get the processed image data
            processed_data = output_buffer.getvalue()
            thumbnail_data = thumbnail_buffer.getvalue()
            
            # Calculate the hash of the processed image
            sticker_hash = hashlib.sha256(processed_data).hexdigest()
            
            # Get MIME type
            mime_type = 'image/webp'
            
            # Create output filename
            filename = os.path.splitext(os.path.basename(file_path))[0]
            output_filename = f"{filename}.webp"
            
            logger.info(f"Sticker processed successfully: {original_dimensions} -> {img.size}")
            
            return {
                'data': processed_data,
                'thumbnail': thumbnail_data,
                'width': img.size[0],
                'height': img.size[1],
                'original_width': original_dimensions[0],
                'original_height': original_dimensions[1],
                'mime_type': mime_type,
                'file_name': output_filename,
                'file_size': len(processed_data),
                'file_hash': sticker_hash,
                'media_type': MEDIA_TYPE_STICKER
            }
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing sticker: {str(e)}")
            raise MediaError(f"Sticker processing failed: {str(e)}")
            
    async def process_incoming_media(self, 
                                    file_path: str, 
                                    media_type: int) -> Dict[str, Any]:
        """
        Process a received media file.
        
        Args:
            file_path: Path to the media file
            media_type: Type of the media
            
        Returns:
            Dictionary with processed media details
            
        Raises:
            MediaError: If processing fails
        """
        logger.info(f"Processing incoming media: {file_path}, type: {media_type}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise MediaError(f"File not found: {file_path}")
                
            # Get basic file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            mime_type = self._get_mime_type(file_path)
            
            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)
            
            result = {
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'mime_type': mime_type,
                'file_hash': file_hash,
                'media_type': media_type
            }
            
            # Process based on media type
            if media_type == MEDIA_TYPE_IMAGE:
                # Extract image dimensions and generate thumbnail
                try:
                    img = Image.open(file_path)
                    width, height = img.size
                    result['width'] = width
                    result['height'] = height
                    
                    # Generate thumbnail
                    thumbnail_buffer = await self._generate_thumbnail(img)
                    result['thumbnail'] = thumbnail_buffer.getvalue()
                    
                    # Extract EXIF data if available
                    if hasattr(img, '_getexif') and img._getexif():
                        exif_data = img._getexif()
                        result['exif'] = self._extract_useful_exif(exif_data)
                except Exception as e:
                    logger.warning(f"Failed to process image details: {str(e)}")
                    
            elif media_type == MEDIA_TYPE_VIDEO:
                # Try to extract video metadata if possible
                try:
                    # This would require additional libraries like opencv or ffmpeg
                    # For now, just try to extract a thumbnail
                    thumbnail_data = await self._extract_video_thumbnail(file_path)
                    if thumbnail_data:
                        result['thumbnail'] = thumbnail_data
                except Exception as e:
                    logger.warning(f"Failed to extract video details: {str(e)}")
                    
            elif media_type == MEDIA_TYPE_AUDIO:
                # Try to extract audio metadata
                try:
                    import mutagen
                    audio = mutagen.File(file_path)
                    if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                        result['duration'] = int(audio.info.length * 1000)  # Convert to milliseconds
                except ImportError:
                    logger.debug("mutagen library not available for audio metadata extraction")
                except Exception as e:
                    logger.warning(f"Failed to extract audio details: {str(e)}")
                    
            logger.info(f"Media processed successfully: {file_path}")
            
            return result
            
        except MediaError:
            # Re-raise MediaError exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing media: {str(e)}")
            raise MediaError(f"Media processing failed: {str(e)}")
            
    async def _generate_thumbnail(self, img: Image.Image) -> io.BytesIO:
        """
        Generate a thumbnail from an image.
        
        Args:
            img: PIL Image object
            
        Returns:
            BytesIO object containing the thumbnail data
            
        Raises:
            MediaError: If thumbnail generation fails
        """
        try:
            # Create a copy of the image
            thumb = img.copy()
            
            # Resize to thumbnail dimensions
            thumb.thumbnail((self.thumbnail_dimension, self.thumbnail_dimension), Image.LANCZOS)
            
            # Create a BytesIO object for the thumbnail
            thumb_buffer = io.BytesIO()
            
            # Save as JPEG with reduced quality
            thumb.save(thumb_buffer, format='JPEG', quality=70)
            
            # Reset buffer position
            thumb_buffer.seek(0)
            
            return thumb_buffer
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            raise MediaError(f"Thumbnail generation failed: {str(e)}")
            
    async def _extract_video_thumbnail(self, file_path: str) -> Optional[bytes]:
        """
        Extract a thumbnail from a video file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Thumbnail image data as bytes, or None if extraction fails
        """
        try:
            # Try to use opencv if available
            try:
                import cv2
                
                # Open the video file
                video = cv2.VideoCapture(file_path)
                
                # Check if video opened successfully
                if not video.isOpened():
                    logger.warning(f"Could not open video file: {file_path}")
                    return None
                    
                # Read the first frame
                success, frame = video.read()
                if not success:
                    logger.warning(f"Could not read frame from video: {file_path}")
                    return None
                    
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Create PIL Image
                img = Image.fromarray(frame_rgb)
                
                # Generate thumbnail
                thumb_buffer = await self._generate_thumbnail(img)
                
                # Get thumbnail data
                return thumb_buffer.getvalue()
                
            except ImportError:
                logger.debug("opencv-python not available for video thumbnail extraction")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to extract video thumbnail: {str(e)}")
            return None
            
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
        
    def _get_mime_type_from_format(self, pil_format: str) -> str:
        """
        Get MIME type from PIL format.
        
        Args:
            pil_format: PIL format string (JPEG, PNG, etc.)
            
        Returns:
            MIME type string
        """
        format_map = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'WEBP': 'image/webp',
            'BMP': 'image/bmp'
        }
        
        return format_map.get(pil_format, 'application/octet-stream')
        
    def _get_extension_from_format(self, pil_format: str) -> str:
        """
        Get file extension from PIL format.
        
        Args:
            pil_format: PIL format string (JPEG, PNG, etc.)
            
        Returns:
            File extension string
        """
        format_map = {
            'JPEG': 'jpg',
            'PNG': 'png',
            'GIF': 'gif',
            'WEBP': 'webp',
            'BMP': 'bmp'
        }
        
        return format_map.get(pil_format, 'bin')
        
    def _exif_dict_to_bytes(self, exif_dict: Dict) -> bytes:
        """
        Convert EXIF dictionary to bytes for embedding in images.
        
        Args:
            exif_dict: EXIF data dictionary
            
        Returns:
            EXIF data as bytes
            
        Raises:
            MediaError: If conversion fails
        """
        try:
            from PIL import TiffImagePlugin
            
            exif_bytes = TiffImagePlugin.ImageFileDirectory_v2()
            
            for tag, value in exif_dict.items():
                if isinstance(tag, int):
                    exif_bytes[tag] = value
                    
            return exif_bytes.tobytes()
            
        except Exception as e:
            logger.warning(f"Failed to convert EXIF data to bytes: {str(e)}")
            return b''
            
    def _extract_useful_exif(self, exif_dict: Dict) -> Dict[str, Any]:
        """
        Extract useful EXIF data from a raw EXIF dictionary.
        
        Args:
            exif_dict: Raw EXIF data dictionary
            
        Returns:
            Dictionary with useful EXIF information
        """
        useful_tags = {
            'DateTime': None,
            'DateTimeOriginal': None,
            'Make': None,
            'Model': None,
            'GPSInfo': None,
            'Orientation': None
        }
        
        try:
            # Map EXIF tag numbers to names
            tag_names = {v: k for k, v in ExifTags.TAGS.items()}
            
            for tag, value in exif_dict.items():
                tag_name = ExifTags.TAGS.get(tag)
                if tag_name in useful_tags:
                    useful_tags[tag_name] = value
                    
            # Process GPS info if available
            if useful_tags['GPSInfo']:
                gps_info = {}
                for key, val in useful_tags['GPSInfo'].items():
                    gps_tag_name = ExifTags.GPSTAGS.get(key, key)
                    gps_info[gps_tag_name] = val
                    
                useful_tags['GPSInfo'] = gps_info
                
            return {k: v for k, v in useful_tags.items() if v is not None}
            
        except Exception as e:
            logger.warning(f"Error extracting EXIF data: {str(e)}")
            return {}
