"""
Tests for the authentication module.
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path to import bocksup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bocksup.auth.authenticator import Authenticator
from bocksup.common.exceptions import AuthenticationError

class TestAuthenticator(unittest.TestCase):
    """Test cases for the Authenticator class."""
    
    def setUp(self):
        """Set up test environment."""
        self.phone_number = "1234567890"
        self.password = "test_password"
        self.authenticator = Authenticator(self.phone_number, self.password)
        
    def test_init(self):
        """Test initialization of Authenticator."""
        self.assertEqual(self.authenticator.phone_number, self.phone_number)
        self.assertEqual(self.authenticator.password, self.password)
        self.assertIsNone(self.authenticator.client_token)
        self.assertIsNone(self.authenticator.server_token)
        self.assertEqual(self.authenticator.expires, 0)
        
    @patch('aiohttp.ClientSession.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication."""
        # Set up mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'client_token': 'test_client_token',
            'server_token': 'test_server_token',
            'expires_in': 3600
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Run test
        async def run_test():
            result = await self.authenticator.authenticate()
            self.assertTrue(result)
            self.assertEqual(self.authenticator.client_token, 'test_client_token')
            self.assertEqual(self.authenticator.server_token, 'test_server_token')
            self.assertGreater(self.authenticator.expires, 0)
            
        asyncio.run(run_test())
        
    @patch('aiohttp.ClientSession.post')
    def test_authenticate_failure(self, mock_post):
        """Test failed authentication."""
        # Set up mock response
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text.return_value = 'Authentication failed'
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Run test
        async def run_test():
            with self.assertRaises(AuthenticationError):
                await self.authenticator.authenticate()
                
        asyncio.run(run_test())
        
    def test_is_authenticated(self):
        """Test is_authenticated method."""
        # Not authenticated initially
        self.assertFalse(self.authenticator.is_authenticated())
        
        # Set tokens and expiration
        self.authenticator.client_token = 'test_client_token'
        self.authenticator.server_token = 'test_server_token'
        self.authenticator.expires = 9999999999  # Far in the future
        
        # Should be authenticated now
        self.assertTrue(self.authenticator.is_authenticated())
        
        # Expired token
        self.authenticator.expires = 1  # In the past
        self.assertFalse(self.authenticator.is_authenticated())
        
    @patch('aiohttp.ClientSession.post')
    def test_refresh_authentication(self, mock_post):
        """Test refresh_authentication method."""
        # Set up mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'client_token': 'new_client_token',
            'server_token': 'new_server_token',
            'expires_in': 3600
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Run test
        async def run_test():
            # Set expired tokens
            self.authenticator.client_token = 'old_client_token'
            self.authenticator.server_token = 'old_server_token'
            self.authenticator.expires = 1  # In the past
            
            # Should trigger a refresh
            result = await self.authenticator.refresh_authentication()
            self.assertTrue(result)
            self.assertEqual(self.authenticator.client_token, 'new_client_token')
            self.assertEqual(self.authenticator.server_token, 'new_server_token')
            
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
