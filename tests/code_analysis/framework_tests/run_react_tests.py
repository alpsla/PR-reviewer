"""Run React-specific tests for TypeScript analyzer."""

import unittest
from tests.code_analysis.framework_tests.test_react import ReactFrameworkTest

if __name__ == '__main__':
    # Create a test suite containing just the React tests
    suite = unittest.TestLoader().loadTestsFromTestCase(ReactFrameworkTest)
    
    # Run the tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
