"""
Settings configuration for Bocksup.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Settings:
    """
    Configuration settings for the Bocksup library.
    
    This class manages global settings and configuration options for the library,
    including connection parameters, logging, and feature flags.
    """
    
    DEFAULT_SETTINGS = {
        # Connection settings
        'connection': {
            'server': 'e1.whatsapp.net',
            'port': 443,
            'use_ssl': True,
            'timeout': 30,
            'ping_interval': 60,
            'max_retries': 5,
            'retry_delay': 5
        },
        
        # Authentication settings
        'auth': {
            'credential_store': None,
            'token_refresh_margin': 300,  # seconds before expiry to refresh
        },
        
        # Message settings
        'messaging': {
            'auto_retry_failed': True,
            'max_message_size': 1024 * 1024,  # 1MB
            'receipt_timeout': 30,
            'delivery_receipts': True,
            'read_receipts': True
        },
        
        # Media settings
        'media': {
            'auto_download': True,
            'max_download_size': 20 * 1024 * 1024,  # 20MB
            'allowed_types': ['image', 'audio', 'video', 'document'],
            'upload_chunk_size': 512 * 1024,  # 512KB
            'download_path': './media',
            'image_quality': 70  # JPEG quality for sent images
        },
        
        # Encryption settings
        'encryption': {
            'enabled': True,
            'key_store_path': './keys',
            'verify_identities': True
        },
        
        # Contact settings
        'contacts': {
            'auto_sync': True,
            'sync_interval': 3600,  # 1 hour
            'store_path': './contacts'
        },
        
        # Group settings
        'groups': {
            'auto_accept_invites': True,
            'auto_sync': True
        },
        
        # Status settings
        'status': {
            'auto_receive': True,
            'auto_mark_seen': True
        },
        
        # Logging settings
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': None
        },
        
        # Debug settings
        'debug': {
            'protocol_trace': False,
            'save_messages': False,
            'save_media': False
        },
        
        # Advanced settings
        'advanced': {
            'socket_impl': 'asyncio',
            'use_websockets': True,
            'proxy': None
        }
    }
    
    def __init__(self, custom_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize settings with optional custom overrides.
        
        Args:
            custom_settings: Dictionary of custom settings to override defaults
        """
        self._settings = self._merge_settings(self.DEFAULT_SETTINGS, custom_settings or {})
        self._configure_logging()
        
    def _merge_settings(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge custom settings with defaults.
        
        Args:
            default: Default settings dictionary
            custom: Custom settings to override defaults
            
        Returns:
            Merged settings dictionary
        """
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _configure_logging(self):
        """
        Configure logging based on settings.
        """
        log_config = self._settings['logging']
        log_level = getattr(logging, log_config['level'].upper(), logging.INFO)
        
        log_format = log_config['format']
        log_file = log_config.get('file')
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            filename=log_file
        )
        
        # Set specific logger levels
        if self._settings['debug']['protocol_trace']:
            logging.getLogger('bocksup.layers.protocol').setLevel(logging.DEBUG)
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            section: Settings section name
            key: Setting key name
            default: Default value if setting is not found
            
        Returns:
            Setting value or default
        """
        try:
            return self._settings[section][key]
        except KeyError:
            return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            section: Settings section name
            key: Setting key name
            value: Value to set
        """
        if section not in self._settings:
            self._settings[section] = {}
            
        self._settings[section][key] = value
        
        # Reconfigure logging if logging settings changed
        if section == 'logging':
            self._configure_logging()
    
    def from_env(self) -> None:
        """
        Load settings from environment variables.
        
        Environment variables should be in the format BOCKSUP_SECTION_KEY.
        For example, BOCKSUP_CONNECTION_TIMEOUT for connection.timeout.
        """
        prefix = 'BOCKSUP_'
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix):].lower().split('_', 1)
                if len(parts) == 2:
                    section, setting = parts
                    
                    # Try to convert value to appropriate type
                    if value.lower() in ('true', 'yes', '1'):
                        value = True
                    elif value.lower() in ('false', 'no', '0'):
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                        value = float(value)
                        
                    self.set(section, setting, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to a dictionary.
        
        Returns:
            Dictionary of all settings
        """
        return self._settings.copy()
