"""
Tests for the authentication module.
"""

import unittest
import requests
from unittest.mock import patch, MagicMock
from scraper.auth import authenticate, get_session, AuthenticationError
from scraper.config import AUTH_CREDENTIALS

class TestAuthentication(unittest.TestCase):
    """Test cases for authentication module."""
    
    def test_get_session(self):
        """Test get_session function."""
        session = get_session()
        self.assertIsInstance(session, requests.Session)
        self.assertIn('User-Agent', session.headers)
    
    @patch('scraper.auth.requests.Session')
    def test_authenticate_success(self, mock_session_class):
        """Test successful authentication."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_get_response = MagicMock()
        mock_get_response.text = '<html><input name="csrf_token" value="test_token"></html>'
        mock_session.get.return_value = mock_get_response
        
        mock_post_response = MagicMock()
        mock_post_response.headers = {'Set-Cookie': 'auth=test'}
        mock_post_response.cookies = {'auth': 'test'}
        mock_session.post.return_value = mock_post_response
        
        result = authenticate()
        
        self.assertEqual(result, mock_session)
        mock_session.get.assert_called_once()
        mock_session.post.assert_called_once()
    
    @patch('scraper.auth.requests.Session')
    def test_authenticate_failure(self, mock_session_class):
        """Test authentication failure."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_get_response = MagicMock()
        mock_get_response.text = '<html></html>'
        mock_session.get.return_value = mock_get_response
        
        mock_post_response = MagicMock()
        mock_post_response.headers = {}
        mock_post_response.cookies = {}
        mock_post_response.text = '<html><div class="error">Invalid credentials</div></html>'
        mock_session.post.return_value = mock_post_response
        
        with self.assertRaises(AuthenticationError):
            authenticate()
    
    @patch('scraper.auth.requests.Session')
    def test_authenticate_request_exception(self, mock_session_class):
        """Test authentication with request exception."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_session.get.side_effect = requests.RequestException("Connection error")
        
        with self.assertRaises(AuthenticationError):
            authenticate()

if __name__ == '__main__':
    unittest.main()
