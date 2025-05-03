"""
Authentication module for 1point3acres website.
"""

import requests
import logging
import time
from bs4 import BeautifulSoup
from .config import LOGIN_URL, DEFAULT_HEADERS, AUTH_CREDENTIALS

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Exception raised for authentication errors."""
    pass

def get_session():
    """
    Create and return a new requests session with default headers.
    
    Returns:
        requests.Session: A session object with default headers.
    """
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session

def authenticate(session=None, credentials=None):
    """
    Authenticate with the 1point3acres website.
    
    Args:
        session (requests.Session, optional): Session to use for authentication.
            If None, a new session will be created.
        credentials (dict, optional): Dictionary containing 'username' and 'password'.
            If None, default credentials from config will be used.
    
    Returns:
        requests.Session: Authenticated session.
    
    Raises:
        AuthenticationError: If authentication fails.
    """
    if session is None:
        session = get_session()
    
    if credentials is None:
        credentials = AUTH_CREDENTIALS
    
    try:
        response = session.get(LOGIN_URL, timeout=30)
        response.raise_for_status()
        
        login_data = {
            'username': credentials['username'],
            'password': credentials['password'],
            'remember': 'on',  # Remember login
            'redirect': ''  # Redirect URL after login
        }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            login_data['csrf_token'] = csrf_token.get('value')
        
        login_response = session.post(
            LOGIN_URL,
            data=login_data,
            timeout=30,
            allow_redirects=True
        )
        login_response.raise_for_status()
        
        if 'Set-Cookie' in login_response.headers and ('auth' in login_response.cookies or 'user' in login_response.cookies):
            logger.info("Authentication successful")
            return session
        else:
            soup = BeautifulSoup(login_response.text, 'html.parser')
            error_msg = soup.find('div', {'class': 'error'})
            if error_msg:
                error_text = error_msg.get_text(strip=True)
                raise AuthenticationError(f"Login failed: {error_text}")
            else:
                raise AuthenticationError("Login failed: Unknown error")
    
    except requests.RequestException as e:
        raise AuthenticationError(f"Authentication request failed: {str(e)}")
    except Exception as e:
        raise AuthenticationError(f"Authentication failed: {str(e)}")
