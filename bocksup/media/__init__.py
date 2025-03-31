"""
Media handling module for WhatsApp.

This module provides functionality for handling media messages in WhatsApp,
including uploading, downloading, and processing images, audio, video, etc.
"""

from bocksup.media.uploader import MediaUploader
from bocksup.media.downloader import MediaDownloader
from bocksup.media.processor import MediaProcessor

__all__ = ['MediaUploader', 'MediaDownloader', 'MediaProcessor']
