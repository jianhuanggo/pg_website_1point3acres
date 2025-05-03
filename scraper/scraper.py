"""
Scraper module for extracting thread data from 1point3acres website.
"""

import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

from .config import (
    BASE_URL, INTERVIEW_BASE_URL, DEFAULT_HEADERS, 
    REQUEST_TIMEOUT, RETRY_COUNT, RETRY_DELAY,
    OUTPUT_DIR, THREAD_OUTPUT_FILE
)
from .auth import authenticate, get_session, AuthenticationError

logger = logging.getLogger(__name__)

class ScraperError(Exception):
    """Exception raised for scraper errors."""
    pass

class ThreadScraper:
    """
    Scraper for 1point3acres interview threads.
    """
    
    def __init__(self, session=None):
        """
        Initialize the scraper.
        
        Args:
            session (requests.Session, optional): Authenticated session.
                If None, a new session will be created and authenticated.
        """
        self.session = session if session else authenticate()
        self.threads = []
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
    def get_thread_page(self, thread_id):
        """
        Get the HTML content of a thread page.
        
        Args:
            thread_id (str): Thread ID.
        
        Returns:
            str: HTML content of the thread page.
        
        Raises:
            ScraperError: If the request fails.
        """
        url = f"{INTERVIEW_BASE_URL}?key=thread&tid={thread_id}"
        
        for attempt in range(RETRY_COUNT):
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                if "Cloudflare" in response.text or "challenge" in response.text:
                    logger.warning(f"Cloudflare protection detected on attempt {attempt+1}")
                    if attempt < RETRY_COUNT - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        raise ScraperError("Cloudflare protection could not be bypassed")
                
                return response.text
            
            except requests.RequestException as e:
                logger.error(f"Request failed on attempt {attempt+1}: {str(e)}")
                if attempt < RETRY_COUNT - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise ScraperError(f"Failed to get thread page after {RETRY_COUNT} attempts: {str(e)}")
    
    def extract_thread_content(self, html):
        """
        Extract thread content from HTML.
        
        Args:
            html (str): HTML content of the thread page.
        
        Returns:
            dict: Thread data including title, author, date, and content.
        
        Raises:
            ScraperError: If content extraction fails.
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            title_elem = soup.find('h1', class_='ts')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
            
            author_elem = soup.find('a', class_='xw1')
            author = author_elem.get_text(strip=True) if author_elem else "Unknown Author"
            
            date_elem = soup.find('span', class_='xi1')
            date = date_elem.get_text(strip=True) if date_elem else "Unknown Date"
            
            content_elem = soup.find('div', class_='t_fsz')
            content = ""
            if content_elem:
                for script in content_elem.find_all(['script', 'style']):
                    script.decompose()
                
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = "No content found"
            
            comments = []
            comment_elems = soup.find_all('div', class_='pstl')
            for comment_elem in comment_elems:
                comment_author_elem = comment_elem.find('a', class_='xi2')
                comment_author = comment_author_elem.get_text(strip=True) if comment_author_elem else "Unknown"
                
                comment_content_elem = comment_elem.find('div', class_='psti')
                comment_content = comment_content_elem.get_text(separator='\n', strip=True) if comment_content_elem else ""
                
                comments.append({
                    'author': comment_author,
                    'content': comment_content
                })
            
            return {
                'title': title,
                'author': author,
                'date': date,
                'content': content,
                'comments': comments
            }
            
        except Exception as e:
            raise ScraperError(f"Failed to extract thread content: {str(e)}")
    
    def get_thread_list(self, page_url):
        """
        Get a list of thread IDs from a page.
        
        Args:
            page_url (str): URL of the page containing thread links.
        
        Returns:
            list: List of thread IDs.
        
        Raises:
            ScraperError: If the request fails.
        """
        try:
            response = self.session.get(page_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            thread_links = soup.find_all('a', href=lambda href: href and 'tid=' in href)
            
            thread_ids = []
            for link in thread_links:
                href = link.get('href')
                parsed_url = urlparse(href)
                query_params = parse_qs(parsed_url.query)
                
                if 'tid' in query_params:
                    thread_id = query_params['tid'][0]
                    if thread_id not in thread_ids:
                        thread_ids.append(thread_id)
            
            return thread_ids
            
        except requests.RequestException as e:
            raise ScraperError(f"Failed to get thread list: {str(e)}")
        except Exception as e:
            raise ScraperError(f"Failed to extract thread IDs: {str(e)}")
    
    def scrape_thread(self, thread_id):
        """
        Scrape a thread and return its content.
        
        Args:
            thread_id (str): Thread ID.
        
        Returns:
            dict: Thread data.
        
        Raises:
            ScraperError: If scraping fails.
        """
        try:
            html = self.get_thread_page(thread_id)
            thread_data = self.extract_thread_content(html)
            thread_data['id'] = thread_id
            self.threads.append(thread_data)
            return thread_data
        except Exception as e:
            raise ScraperError(f"Failed to scrape thread {thread_id}: {str(e)}")
    
    def scrape_threads(self, thread_ids):
        """
        Scrape multiple threads.
        
        Args:
            thread_ids (list): List of thread IDs.
        
        Returns:
            list: List of thread data.
        """
        results = []
        for thread_id in thread_ids:
            try:
                thread_data = self.scrape_thread(thread_id)
                results.append(thread_data)
                logger.info(f"Successfully scraped thread {thread_id}")
                time.sleep(1)  # Be nice to the server
            except ScraperError as e:
                logger.error(f"Error scraping thread {thread_id}: {str(e)}")
        
        return results
    
    def save_threads_to_file(self, output_file=None):
        """
        Save scraped threads to a text file.
        
        Args:
            output_file (str, optional): Path to output file.
                If None, default path from config will be used.
        
        Returns:
            str: Path to the output file.
        """
        if output_file is None:
            output_file = os.path.join(OUTPUT_DIR, THREAD_OUTPUT_FILE)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for thread in self.threads:
                f.write(f"Thread ID: {thread.get('id', 'Unknown')}\n")
                f.write(f"Title: {thread.get('title', 'Unknown Title')}\n")
                f.write(f"Author: {thread.get('author', 'Unknown Author')}\n")
                f.write(f"Date: {thread.get('date', 'Unknown Date')}\n")
                f.write("\nContent:\n")
                f.write(thread.get('content', 'No content'))
                f.write("\n\nComments:\n")
                
                for i, comment in enumerate(thread.get('comments', []), 1):
                    f.write(f"\n--- Comment {i} ---\n")
                    f.write(f"Author: {comment.get('author', 'Unknown')}\n")
                    f.write(f"Content: {comment.get('content', '')}\n")
                
                f.write("\n" + "="*80 + "\n\n")
        
        logger.info(f"Saved {len(self.threads)} threads to {output_file}")
        return output_file
