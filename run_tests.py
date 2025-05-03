"""
Script to run all tests for the 1point3acres scraper.
"""

import os
import sys
import unittest
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_tests():
    """
    Run all tests and return success status.
    
    Returns:
        bool: True if all tests pass, False otherwise.
    """
    os.environ['ONEPOINT3ACRES_USERNAME'] = 'test_user'
    os.environ['ONEPOINT3ACRES_PASSWORD'] = 'test_password'
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'scraper', 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    logger.info("Running tests for 1point3acres scraper...")
    success = run_tests()
    
    if success:
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Some tests failed!")
        sys.exit(1)
