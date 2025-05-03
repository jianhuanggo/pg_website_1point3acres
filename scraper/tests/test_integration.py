"""
Integration tests for the 1point3acres scraper.
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from scraper.auth import authenticate
from scraper.scraper import ThreadScraper
from scraper.config import get_auth_credentials

class TestIntegration(unittest.TestCase):
    """Integration test cases for the scraper."""
    
    @patch('scraper.auth.requests.Session')
    def test_end_to_end(self, mock_session_class):
        """Test the entire scraping process."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_get_response = MagicMock()
        mock_get_response.text = '<html><input name="csrf_token" value="test_token"></html>'
        mock_session.get.return_value = mock_get_response
        
        mock_post_response = MagicMock()
        mock_post_response.headers = {'Set-Cookie': 'auth=test'}
        mock_post_response.cookies = {'auth': 'test'}
        mock_session.post.return_value = mock_post_response
        
        thread_list_html = """
        <html>
            <body>
                <a href="?key=thread&tid=123">Thread 1</a>
                <a href="?key=thread&tid=456">Thread 2</a>
            </body>
        </html>
        """
        
        thread_html = """
        <html>
            <head><title>Test Thread</title></head>
            <body>
                <h1 class="ts">Test Thread Title</h1>
                <a class="xw1">Test Author</a>
                <span class="xi1">2023-01-01</span>
                <div class="t_fsz">
                    <p>This is the main content of the thread.</p>
                </div>
                <div class="pstl">
                    <a class="xi2">Comment Author</a>
                    <div class="psti">This is a comment</div>
                </div>
            </body>
        </html>
        """
        
        def mock_get_side_effect(url, **kwargs):
            response = MagicMock()
            if 'tid=123' in url or 'tid=456' in url:
                response.text = thread_html
            else:
                response.text = thread_list_html
            return response
        
        mock_session.get.side_effect = mock_get_side_effect
        
        session = authenticate()
        
        scraper = ThreadScraper(session)
        
        thread_ids = scraper.get_thread_list("test_url")
        self.assertEqual(len(thread_ids), 2)
        
        scraper.scrape_threads(thread_ids)
        self.assertEqual(len(scraper.threads), 2)
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            output_file = scraper.save_threads_to_file(temp_path)
            self.assertTrue(os.path.exists(output_file))
            
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Thread ID: 123', content)
                self.assertIn('Thread ID: 456', content)
                self.assertIn('Test Thread Title', content)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @unittest.skip("Skip live test by default")
    def test_live_authentication(self):
        """Test live authentication with real credentials."""
        try:
            session = authenticate()
            self.assertIsNotNone(session)
            self.assertIsInstance(session.cookies, dict)
            self.assertTrue(len(session.cookies) > 0)
        except Exception as e:
            self.fail(f"Authentication failed: {str(e)}")
    
    @unittest.skip("Skip live test by default")
    def test_live_thread_scraping(self):
        """Test live thread scraping with real website."""
        try:
            session = authenticate()
            
            scraper = ThreadScraper(session)
            
            thread_data = scraper.scrape_thread("1127012")
            
            self.assertEqual(thread_data['id'], "1127012")
            self.assertIsNotNone(thread_data['title'])
            self.assertIsNotNone(thread_data['content'])
        except Exception as e:
            self.fail(f"Thread scraping failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
