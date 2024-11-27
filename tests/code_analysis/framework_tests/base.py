"""Base class for framework-specific tests."""

import unittest
import os
import shutil
from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer

class BaseFrameworkTest(unittest.TestCase):
    """Base class for framework-specific TypeScript tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Set up logging for tests
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize logging with test configuration
        from logging_config import setup_logging
        setup_logging(
            log_level="DEBUG",
            app_name="typescript_analyzer_test",
            max_bytes=1024 * 1024,  # 1MB
            backup_count=3,
            log_to_console=True
        )
    
    def setUp(self):
        """Set up test case."""
        self.analyzer = TypeScriptAnalyzer()
        self.test_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'test_files', 'typescript')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Framework-specific directory
        self.framework_dir = os.path.join(self.test_dir, self.__class__.__name__.lower().replace('frameworktest', ''))
        os.makedirs(self.framework_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test files."""
        try:
            if os.path.exists(self.framework_dir):
                shutil.rmtree(self.framework_dir)
        except Exception as e:
            print(f"Error cleaning up test files: {e}")
    
    def analyze_file(self, filename: str) -> dict:
        """Analyze a test file and return the results."""
        filepath = os.path.join(self.framework_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.analyzer.analyze_file(content, filepath).to_dict()
    
    def assertFrameworkDetected(self, analysis: dict, framework: str):
        """Assert that the correct framework was detected."""
        framework_analysis = analysis.get('framework_analysis', {})
        self.assertEqual(framework_analysis.get('framework', ''), framework,
                        f"Expected {framework} framework to be detected")
