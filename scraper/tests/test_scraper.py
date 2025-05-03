"""
Tests for the scraper module.
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from scraper.scraper import ThreadScraper, ScraperError
from scraper.config import INTERVIEW_BASE_URL

class TestThreadScraper(unittest.TestCase):
    """Test cases for ThreadScraper class."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_session = MagicMock()
        self.scraper = ThreadScraper(self.mock_session)
        
        self.sample_html = """
        <html>
            <head><title>Test Thread</title></head>
            <body>
                <h1 class="ts">Test Thread Title</h1>
                <a class="xw1">Test Author</a>
                <span class="xi1">2023-01-01</span>
                <div class="t_fsz">
                    <p>This is the main content of the thread.</p>
                    <p>It contains multiple paragraphs.</p>
                </div>
                <div class="pstl">
                    <a class="xi2">Comment Author 1</a>
                    <div class="psti">This is comment 1</div>
                </div>
                <div class="pstl">
                    <a class="xi2">Comment Author 2</a>
                    <div class="psti">This is comment 2</div>
                </div>
            </body>
        </html>
        """
        
        self.thread_list_html = """
        <html>
            <body>
                <a href="?key=thread&tid=123">Thread 1</a>
                <a href="?key=thread&tid=456">Thread 2</a>
                <a href="?key=thread&tid=789">Thread 3</a>
                <a href="?key=thread&tid=123">Duplicate Thread</a>
            </body>
        </html>
        """
    
    def test_get_thread_page_success(self):
        """Test successful thread page retrieval."""
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        self.mock_session.get.return_value = mock_response
        
        result = self.scraper.get_thread_page("123")
        
        self.assertEqual(result, self.sample_html)
        self.mock_session.get.assert_called_with(
            f"{INTERVIEW_BASE_URL}?key=thread&tid=123",
            timeout=30
        )
    
    def test_get_thread_page_cloudflare(self):
        """Test thread page retrieval with Cloudflare protection."""
        mock_response = MagicMock()
        mock_response.text = "Cloudflare protection"
        self.mock_session.get.return_value = mock_response
        
        with self.assertRaises(ScraperError):
            self.scraper.get_thread_page("123")
    
    def test_extract_thread_content(self):
        """Test thread content extraction."""
        result = self.scraper.extract_thread_content(self.sample_html)
        
        self.assertEqual(result['title'], "Test Thread Title")
        self.assertEqual(result['author'], "Test Author")
        self.assertEqual(result['date'], "2023-01-01")
        self.assertIn("This is the main content of the thread.", result['content'])
        self.assertEqual(len(result['comments']), 2)
        self.assertEqual(result['comments'][0]['author'], "Comment Author 1")
        self.assertEqual(result['comments'][0]['content'], "This is comment 1")
    
    def test_get_thread_list(self):
        """Test thread list retrieval."""
        mock_response = MagicMock()
        mock_response.text = self.thread_list_html
        self.mock_session.get.return_value = mock_response
        
        result = self.scraper.get_thread_list("test_url")
        
        self.assertEqual(len(result), 3)  # Should deduplicate
        self.assertIn("123", result)
        self.assertIn("456", result)
        self.assertIn("789", result)
    
    def test_scrape_thread(self):
        """Test thread scraping."""
        with patch.object(self.scraper, 'get_thread_page', return_value=self.sample_html):
            result = self.scraper.scrape_thread("123")
            
            self.assertEqual(result['id'], "123")
            self.assertEqual(result['title'], "Test Thread Title")
            self.assertEqual(len(self.scraper.threads), 1)
    
    def test_save_threads_to_file(self):
        """Test saving threads to file."""
        self.scraper.threads = [
            {
                'id': '123',
                'title': 'Test Thread',
                'author': 'Test Author',
                'date': '2023-01-01',
                'content': 'Test content',
                'comments': [
                    {'author': 'Comment Author', 'content': 'Test comment'}
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = self.scraper.save_threads_to_file(temp_path)
            
            self.assertEqual(result, temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Thread ID: 123', content)
                self.assertIn('Title: Test Thread', content)
                self.assertIn('Author: Test Author', content)
                self.assertIn('Test content', content)
                self.assertIn('Comment Author', content)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()
