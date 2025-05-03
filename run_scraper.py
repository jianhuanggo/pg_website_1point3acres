"""
Script to run the 1point3acres scraper.
"""

import os
import sys
import logging
import argparse
from scraper.auth import authenticate, AuthenticationError
from scraper.scraper import ThreadScraper, ScraperError
from scraper.config import INTERVIEW_BASE_URL, OUTPUT_DIR, THREAD_OUTPUT_FILE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Scrape threads from 1point3acres website.')
    parser.add_argument(
        '--thread-id',
        type=str,
        help='Specific thread ID to scrape'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default=os.path.join(OUTPUT_DIR, THREAD_OUTPUT_FILE),
        help='Path to output file'
    )
    parser.add_argument(
        '--page-url',
        type=str,
        default=f"{INTERVIEW_BASE_URL}?key=thread&tid=1127012",
        help='URL of the page containing thread links'
    )
    return parser.parse_args()

def main():
    """
    Main function to run the scraper.
    
    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    args = parse_args()
    
    try:
        logger.info("Running tests...")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from run_tests import run_tests
        
        if not run_tests():
            logger.error("Tests failed. Aborting scraper run.")
            return 1
        
        logger.info("Tests passed. Starting scraper...")
        
        logger.info("Authenticating with 1point3acres...")
        session = authenticate()
        
        scraper = ThreadScraper(session)
        
        if args.thread_id:
            logger.info(f"Scraping thread {args.thread_id}...")
            scraper.scrape_thread(args.thread_id)
        else:
            logger.info(f"Getting thread list from {args.page_url}...")
            thread_ids = scraper.get_thread_list(args.page_url)
            logger.info(f"Found {len(thread_ids)} threads")
            
            logger.info("Scraping threads...")
            scraper.scrape_threads(thread_ids)
        
        output_file = scraper.save_threads_to_file(args.output_file)
        logger.info(f"Threads saved to {output_file}")
        
        return 0
    
    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        return 1
    except ScraperError as e:
        logger.error(f"Scraper error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
